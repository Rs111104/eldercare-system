from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, Response
import os
import asyncio
import time
import logging
import httpx
import hmac
import hashlib
import json
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client import Histogram

app = FastAPI(title="Alert Automation Service")
logger = logging.getLogger("automation")
logging.basicConfig(level=logging.INFO)


@app.get("/health")
async def health():
    return {"status": "ok"}

# Simple in-memory dedupe cache: key -> expiry
_DEDUPE_CACHE = {}
_DEDUPE_LOCK = asyncio.Lock()
_DEDUPE_TTL = int(os.environ.get("AUTOMATION_DEDUPE_TTL", "300"))

async def _cleanup_cache():
    now = time.time()
    keys = [k for k, exp in _DEDUPE_CACHE.items() if exp <= now]
    for k in keys:
        _DEDUPE_CACHE.pop(k, None)

async def _is_duplicate(key: str) -> bool:
    async with _DEDUPE_LOCK:
        await _cleanup_cache()
        if key in _DEDUPE_CACHE:
            return True
        _DEDUPE_CACHE[key] = time.time() + _DEDUPE_TTL
        return False

async def _forward_to_slack(text: str):
    webhook = os.environ.get("ALERT_SLACK_WEBHOOK")
    if not webhook:
        logger.debug("No Slack webhook configured; skipping")
        return
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(webhook, json={"text": text})

async def _forward_to_pagerduty(summary: str, source: str = "automation"):
    key = os.environ.get("PAGERDUTY_INTEGRATION_KEY")
    if not key:
        logger.debug("No PagerDuty key configured; skipping")
        return
    payload = {
        "routing_key": key,
        "event_action": "trigger",
        "payload": {
            "summary": summary,
            "source": source,
            "severity": "error",
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post("https://events.pagerduty.com/v2/enqueue", json=payload)


async def _create_runbook(summary: str, labels: dict, annotations: dict):
    """Create an incident/runbook in GitHub issues if configured via env vars.
    Required env: GITHUB_REPO (owner/repo), GITHUB_TOKEN
    """
    repo = os.environ.get("GITHUB_REPO")
    token = os.environ.get("GITHUB_TOKEN")
    if not repo or not token:
        logger.debug("No GitHub runbook configured; skipping")
        return

    title = f"Incident: {summary}"
    body = f"Labels: {labels}\n\nAnnotations: {annotations}\n\nAuto-created by automation service"
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}
    payload = {"title": title, "body": body}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload, headers=headers)
    except Exception:
        logger.exception("Failed to create GitHub issue for runbook")

# Prometheus metrics
ALERTS_RECEIVED = Counter("automation_alerts_received_total", "Total alerts received")
ALERTS_DUPLICATE = Counter("automation_alerts_duplicate_total", "Total duplicate alerts skipped")
ALERTS_FORWARDED_SLACK = Counter("automation_alerts_forwarded_slack_total", "Alerts forwarded to Slack")
ALERTS_FORWARDED_PAGERDUTY = Counter("automation_alerts_forwarded_pagerduty_total", "Alerts forwarded to PagerDuty")
ALERT_LATENCY = Histogram("automation_alert_processing_seconds", "Alert processing latency seconds")
ALERT_ERRORS = Counter("automation_alert_errors_total", "Total alert handling errors")
ALERT_RUNBOOKS_CREATED = Counter("automation_runbooks_created_total", "Runbooks / incidents created")


def _verify_signature(secret: str, body: bytes, header_value: str) -> bool:
    # header_value expected: sha256=hex
    try:
        if not header_value or not secret:
            return False
        alg, sig = header_value.split("=", 1)
        if alg != "sha256":
            return False
        mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, sig)
    except Exception:
        return False

@app.post("/alert")
async def receive_alert(request: Request):
    start = time.time()
    raw = await request.body()

    # Optional HMAC signature verification OR static token header
    secret = os.environ.get("ALERT_WEBHOOK_SECRET")
    sig_header = request.headers.get("X-Alert-Signature") or request.headers.get("X-Signature")
    token_header = request.headers.get("X-Alert-Token") or request.headers.get("X-Auth-Token")
    if secret:
        valid_sig = _verify_signature(secret, raw, sig_header or "")
        valid_token = token_header == secret
        if not (valid_sig or valid_token):
            ALERT_ERRORS.inc()
            raise HTTPException(status_code=401, detail="Invalid webhook signature or token")

    try:
        payload = json.loads(raw.decode() or "[]")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Alertmanager sends a list of alerts or a dict with key 'alerts'
    if isinstance(payload, dict) and "alerts" in payload:
        alerts = payload["alerts"]
    elif isinstance(payload, list):
        alerts = payload
    else:
        raise HTTPException(status_code=400, detail="Unsupported payload shape")

    ALERTS_RECEIVED.inc(len(alerts))
    results = []
    for a in alerts:
        labels = a.get("labels", {})
        annotations = a.get("annotations", {})
        starts_at = a.get("startsAt") or a.get("start") or ""
        key = f"{labels.get('alertname','')}-{labels.get('instance','')}-{starts_at}"
        duplicate = await _is_duplicate(key)
        summary = annotations.get("summary") or annotations.get("message") or labels.get("alertname","alert")
        entry = {"labels": labels, "summary": summary, "duplicate": duplicate}
        results.append(entry)

        if duplicate:
            ALERTS_DUPLICATE.inc()
            logger.info("Duplicate alert skipped: %s", key)
            continue

        # Build a human-friendly text
        text = f"[{labels.get('severity','info').upper()}] {summary}\nLabels: {labels}\nAnnotations: {annotations}"
        # Forward asynchronously but don't block the response for long
        asyncio.create_task(_forward_to_slack(text))
        ALERTS_FORWARDED_SLACK.inc()
        asyncio.create_task(_forward_to_pagerduty(summary))
        ALERTS_FORWARDED_PAGERDUTY.inc()

        # optional runbook / incident creation for critical alerts
        try:
            severity = labels.get("severity") or labels.get("level") or ""
            if severity.lower() == "critical":
                # create runbook/incident asynchronously
                asyncio.create_task(_create_runbook(summary, labels, annotations))
                ALERT_RUNBOOKS_CREATED.inc()
        except Exception:
            ALERT_ERRORS.inc()
            logger.exception("Runbook creation failed")

    duration = time.time() - start
    try:
        ALERT_LATENCY.observe(duration)
    except Exception:
        pass
    return JSONResponse({"received": len(results), "details": results})


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
