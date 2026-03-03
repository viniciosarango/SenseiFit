from django.conf import settings
from core.services.whatsapp_service import send_whatsapp_template


def send_client_link_whatsapp(*, phone_e164: str, full_name: str, gym_name: str):
    """
    Envía un mensaje por plantilla (la que esté configurada en settings) con link al portal.
    Mientras la plantilla real no esté aprobada, usaremos hello_world para pruebas.
    """
    template = getattr(settings, "WHATSAPP_TEMPLATE_CREDENTIALS", "")
    if not template:
        raise Exception("Falta WHATSAPP_TEMPLATE_CREDENTIALS en settings.")

    frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
    login_url = f"{frontend_url}/auth/login" if frontend_url else ""

    # Ajusta el orden de parámetros según tu plantilla aprobada.
    # Para pruebas con hello_world normalmente NO requiere parámetros.
    body_params = [
        full_name or "Cliente",
        gym_name or "Dorians Gym",
        login_url,
    ]

    return send_whatsapp_template(
        to=phone_e164,
        template_name=template,
        lang="es_EC",
        components=[
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": full_name or "Cliente"},
                    {"type": "text", "text": gym_name or "Dorians Gym"},
                    {"type": "text", "text": login_url},
                ],
            }
        ],
    )