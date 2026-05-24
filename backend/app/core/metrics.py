from typing import Optional

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

    HTTP_REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    HTTP_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency', ['method', 'endpoint'])
    CACHE_HITS = Counter('cache_hits_total', 'Total cache hits', ['key_prefix'])
    CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses', ['key_prefix'])
    CACHE_INVALIDATIONS = Counter('cache_invalidations_total', 'Total cache invalidations')

    def metrics_latest() -> bytes:
        return generate_latest()

    METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
except Exception:
    HTTP_REQUESTS = None
    HTTP_LATENCY = None

    def metrics_latest() -> bytes:
        return b""

    METRICS_CONTENT_TYPE = 'text/plain; version=0.0.4; charset=utf-8'
