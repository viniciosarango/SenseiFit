import requests
from django.conf import settings
from django.core.mail import EmailMessage, get_connection



def send_client_credentials_email(
    *,
    email,
    username,
    temp_password,
    full_name=None,
    login_url=None,
    reply_to=None
):
    if not email:
        return

    subject = "Acceso a tu portal - SenseiFit / Dorian's Gym 🏋️‍♂️"

    name_line = f"Hola {full_name}," if full_name else "Hola,"
    url_line = f"\n\nAccede aquí: {login_url}\n" if login_url else "\nAccede desde: (URL no configurada)\n"

    message = f"""{name_line}

Tu cuenta ha sido creada correctamente.{url_line}
Usuario: {username}
Contraseña temporal (PIN): {temp_password}

Por seguridad y para acceder a tu portal, te pediremos que cambies tu contraseña en el primer ingreso.

Dorian Gym
¡Transforma tu vida! 💪
"""

    msg = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
        reply_to=[reply_to] if reply_to else None,
    )

    # ✅ NO romper creación de cliente si SMTP está bloqueado/lento en PROD
    try:
        timeout = getattr(settings, "EMAIL_TIMEOUT", 5)
        conn = get_connection(timeout=timeout)
        msg.connection = conn
        msg.send(fail_silently=True)
    except Exception:
        pass
    


def send_email_verification_link(*, email, full_name=None, verify_url=None, reply_to=None):
    if not email or not verify_url:
        return

    subject = "Verifica tu email - SenseiFit ✅"
    name_line = f"Hola {full_name}," if full_name else "Hola,"

    message = f"""{name_line}

Para verificar tu correo electrónico, abre este enlace:

{verify_url}

Si tú no solicitaste esto, puedes ignorar este mensaje.

— SenseiFit
"""

    msg = EmailMessage(
        subject=subject,
        body=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email],
        reply_to=[reply_to] if reply_to else None,
    )

    # ✅ NO romper el flujo si SMTP está bloqueado / lento en producción
    try:
        timeout = getattr(settings, "EMAIL_TIMEOUT", 5)
        conn = get_connection(timeout=timeout)
        msg.connection = conn
        msg.send(fail_silently=True)
    except Exception:
        pass



def send_client_credentials_whatsapp(*, full_name, username, temp_password, login_url=None):
    """
    LOCAL/DEV: manda SIEMPRE al WHATSAPP_TEST_TO usando template de prueba.
    Cuando aprueben la plantilla real, cambiamos a enviar al teléfono real del cliente
    y pasamos variables.
    """
    token = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
    phone_number_id = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")
    to_number = getattr(settings, "WHATSAPP_TEST_TO", "")

    template_name = getattr(settings, "WHATSAPP_TEMPLATE_CREDENTIALS", "hello_world")
    template_lang = getattr(settings, "WHATSAPP_TEMPLATE_LANG", "en_US")
    api_version = getattr(settings, "WHATSAPP_API_VERSION", "v22.0")

    if not token or not phone_number_id or not to_number:
        return {"ok": False, "detail": "WhatsApp settings incompletos."}

    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"

    # ✅ IMPORTANTE:
    # "hello_world" NO acepta variables. Por eso aquí solo lo enviamos tal cual.
    payload = {
        "messaging_product": "whatsapp",
        "to": str(to_number),
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": template_lang}
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    r = requests.post(url, json=payload, headers=headers, timeout=20)

    # devolvemos respuesta para debug
    try:
        data = r.json()
    except Exception:
        data = {"raw": r.text}

    if r.status_code >= 400:
        return {"ok": False, "status": r.status_code, "meta": data}

    return {"ok": True, "meta": data}