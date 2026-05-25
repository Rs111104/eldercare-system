from app.services.whatsapp_service import WhatsAppService
from app.core.utils import sanitize_text, looks_malicious
from app.core.security import create_access_token
from app.store import store
from app.config import settings


def test_sanitize_text():
    dirty = '<script>alert(1)</script><b>hello</b>'
    clean = sanitize_text(dirty)
    assert '<' not in clean and '>' not in clean


def test_whatsapp_signature_verification():
    svc = WhatsAppService()
    body = b'{"hello":"world"}'
    # when no secret set, verification should raise configuration error (secret required)
    settings.WHATSAPP_APP_SECRET = ""
    import pytest
    with pytest.raises(RuntimeError):
        svc.verify_webhook_signature("", body)

    # when secret set, compute signature and verify
    settings.WHATSAPP_APP_SECRET = "test-secret"
    import hmac, hashlib

    sig = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
    header = f"sha256={sig}"
    assert svc.verify_webhook_signature(header, body) is True
    assert svc.verify_webhook_signature("sha256=bad", body) is False


def test_require_role_admin():
    # create an admin and issue token
    admin = store.create_admin(phone="+10000000000", name="admin", password="pass")
    token = create_access_token(user_id=admin["id"], phone_number=admin["phone"], user_type="admin")
    # verify token payload
    payload = None
    try:
        from app.core.security import verify_token

        payload = verify_token(token)
    except Exception:
        payload = None
    assert payload is not None
    assert getattr(payload, "user_type", None) == "admin"
