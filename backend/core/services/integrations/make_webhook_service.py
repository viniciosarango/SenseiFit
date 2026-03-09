import requests
from django.conf import settings
from django.utils import timezone


def _truncate_large_strings(value, max_length=1000):
    if isinstance(value, str):
        return value if len(value) <= max_length else value[:max_length] + "..."
    if isinstance(value, dict):
        return {k: _truncate_large_strings(v, max_length=max_length) for k, v in value.items()}
    if isinstance(value, list):
        return [_truncate_large_strings(v, max_length=max_length) for v in value]
    return value



def send_make_event(*, event: str, data: dict):
    """
    Envia un evento a Make (Custom Webhook).
    NO rompe nada si no está configurado.
    """
    url = getattr(settings, "MAKE_WEBHOOK_URL", "") or ""
    secret = getattr(settings, "MAKE_WEBHOOK_SECRET", "") or ""

    if not url:
        return {"skipped": True, "reason": "make_webhook_not_configured"}

    safe_data = _truncate_large_strings(data or {}, max_length=1000)

    payload = {
        "event": event,
        "sent_at": timezone.now().isoformat(),
        "data": safe_data,
    }

    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Make-Secret"] = secret

    try:
        r = requests.post(url, json=payload, headers=headers, timeout=15)
        # No explota el sistema si Make falla
        if r.status_code >= 400:
            return {"skipped": True, "reason": "make_webhook_error", "status_code": r.status_code, "text": r.text[:500]}
        return {"ok": True, "status_code": r.status_code}
    except Exception as e:
        return {"skipped": True, "reason": "make_webhook_exception", "error": str(e)}