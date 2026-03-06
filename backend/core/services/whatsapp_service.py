import requests
from django.conf import settings


def send_whatsapp_template(*, to: str, template_name: str, lang: str = "en_US", components=None):
    """
    Envía plantilla por WhatsApp Cloud API.
    - Si WhatsApp NO está configurado (token/phone_id vacío): NO explota, solo devuelve skipped.
    - Si Meta responde error: NO explota, devuelve skipped con detalle.
    """

    # ✅ APAGADOR GLOBAL (no toca nada más)
    if not getattr(settings, "WHATSAPP_CLOUD_ENABLED", True):
        return {"skipped": True, "reason": "WHATSAPP_CLOUD_ENABLED is False"}

    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "") or ""
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "") or ""
    version = getattr(settings, "WHATSAPP_API_VERSION", "v22.0") or "v22.0"

    print("WA_CFG phone_number_id=", phone_number_id, flush=True)
    print("WA_CFG token_present=", bool(token), flush=True)
    print("WA_CFG version=", version, flush=True)

    # ✅ No romper el sistema si no está configurado
    if not phone_number_id or not token:
        return {"skipped": True, "reason": "whatsapp_not_configured"}

    # Normalizar: Meta acepta sin '+'
    to = str(to).strip().replace("+", "").replace(" ", "")

    url = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": lang},
        },
    }

    if components:
        payload["template"]["components"] = components

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        print("WA_TO_NORMALIZED=", to, flush=True)
        print("WA_URL=", url, flush=True)
        print("WA_PAYLOAD=", payload, flush=True)
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        print("WA_HTTP_STATUS=", r.status_code, flush=True)
        print("WA_HTTP_TEXT=", r.text[:500], flush=True)
        content_type = (r.headers.get("content-type") or "").lower()
        data = r.json() if content_type.startswith("application/json") else {"raw": r.text}
        print("WA_MESSAGE_ID=", (data.get("messages") or [{}])[0].get("id"), flush=True)

        # ✅ No romper el sistema si Meta responde error
        if r.status_code >= 400:
            return {
                "skipped": True,
                "reason": "whatsapp_api_error",
                "status_code": r.status_code,
                "response": data,
            }

        return data

    except Exception as e:
        # ✅ No romper el sistema por timeout/red/etc.
        return {"skipped": True, "reason": "whatsapp_exception", "error": str(e)}