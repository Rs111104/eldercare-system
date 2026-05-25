from typing import Optional

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

    HTTP_REQUESTS = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
    HTTP_LATENCY = Histogram('http_request_latency_seconds', 'HTTP request latency', ['method', 'endpoint'], buckets=(0.025, 0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4))
    CACHE_HITS = Counter('cache_hits_total', 'Total cache hits', ['key_prefix'])
    CACHE_MISSES = Counter('cache_misses_total', 'Total cache misses', ['key_prefix'])
    CACHE_INVALIDATIONS = Counter('cache_invalidations_total', 'Total cache invalidations')
    WHATSAPP_MESSAGES_SENT = Counter('whatsapp_message_sent_total', 'WhatsApp delivery attempts', ['status', 'message_type'])
    TASKS_CREATED = Counter('task_created_total', 'Tasks created', ['service_type', 'status'])
    PAYOUTS_PROCESSED = Counter('payout_processed_total', 'Payout processing attempts', ['status'])
    OPENAI_CALL_DURATION = Histogram('openai_call_duration_seconds', 'OpenAI call duration')
    CELERY_TASK_DURATION = Histogram('celery_task_duration_seconds', 'Celery task duration', ['task_name', 'status'])

    def metrics_latest() -> bytes:
        return generate_latest()

    METRICS_CONTENT_TYPE = CONTENT_TYPE_LATEST
except Exception:
    HTTP_REQUESTS = None
    HTTP_LATENCY = None
    CACHE_HITS = None
    CACHE_MISSES = None
    CACHE_INVALIDATIONS = None
    WHATSAPP_MESSAGES_SENT = None
    TASKS_CREATED = None
    PAYOUTS_PROCESSED = None
    OPENAI_CALL_DURATION = None
    CELERY_TASK_DURATION = None

    def metrics_latest() -> bytes:
        return b""

    METRICS_CONTENT_TYPE = 'text/plain; version=0.0.4; charset=utf-8'
