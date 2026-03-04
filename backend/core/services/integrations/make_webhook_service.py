import requests
from django.conf import settings
from django.utils import timezone


def send_make_event(*, event: str, data: dict):
    """
    Envia un evento a Make (Custom Webhook).
    NO rompe nada si no está configurado.
    """
    url = getattr(settings, "MAKE_WEBHOOK_URL", "") or ""
    secret = getattr(settings, "MAKE_WEBHOOK_SECRET", "") or ""

    if not url:
        return {"skipped": True, "reason": "make_webhook_not_configured"}

    payload = {
        "event": event,
        "sent_at": timezone.now().isoformat(),
        "data": data or {},
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