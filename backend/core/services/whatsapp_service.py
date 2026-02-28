import requests
from django.conf import settings


def send_whatsapp_template(*, to: str, template_name: str, lang: str = "en_US", components=None):
    """
    Envía plantilla por WhatsApp Cloud API.
    En modo PRUEBA, 'to' debe ser un 'test recipient' del sandbox.
    """
    phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
    token = settings.WHATSAPP_ACCESS_TOKEN
    version = getattr(settings, "WHATSAPP_API_VERSION", "v22.0")

    if not phone_number_id or not token:
        raise RuntimeError("Falta WHATSAPP_PHONE_NUMBER_ID o WHATSAPP_ACCESS_TOKEN en settings.")

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

    r = requests.post(url, json=payload, headers=headers, timeout=20)
    data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {"raw": r.text}

    if r.status_code >= 400:
        raise RuntimeError(f"WhatsApp API error {r.status_code}: {data}")

    return data