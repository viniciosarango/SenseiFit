import requests
from django.conf import settings
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape


def send_client_credentials_email(
    *,
    email,
    username,
    temp_password,
    full_name=None,
    login_url=None,
    reply_to=None,
):
    if not email:
        return

    subject = "Acceso a tu portal - Dorian's Gym / SenseiFit 🏋️‍♂️"

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
        reply_to=[reply_to] if reply_to else ["soporte@senseifit.app"],
    )

    # ✅ NO romper creación de cliente si falla el email
    try:
        msg.send(fail_silently=True)
    except Exception:
        pass



def send_email_verification_link(*, email, full_name=None, verify_url=None, reply_to=None):
    if not email or not verify_url:
        return

    subject = "Verifica tu email - SenseiFit ✅"
    name = full_name or "Hola"
    safe_name = escape(name)
    safe_url = escape(verify_url)

    text_body = f"""{name}

Para verificar tu correo electrónico, abre este enlace:

{verify_url}

Si tú no solicitaste esto, puedes ignorar este mensaje.

Dorians Gym — SenseiFit
"""

    html_body = f"""
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f6f7fb;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f7fb;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:14px;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.06);">
            <tr>
              <td style="padding:28px 28px 10px 28px;">
                <h2 style="margin:0 0 8px 0;color:#111827;font-size:20px;">Verifica tu email</h2>
                <p style="margin:0;color:#374151;font-size:14px;line-height:20px;">
                  Hola {safe_name},<br/>
                  Para verificar tu correo electrónico, haz clic en el botón:
                </p>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding:18px 28px;">
                <a href="{safe_url}"
                   style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;
                          padding:12px 18px;border-radius:10px;font-size:14px;font-weight:bold;">
                  Verificar correo
                </a>
              </td>
            </tr>

            <tr>
              <td style="padding:0 28px 22px 28px;">
                <p style="margin:0;color:#6b7280;font-size:12px;line-height:18px;">
                  Si el botón no funciona, copia y pega este enlace en tu navegador:
                  <br/>
                  <span style="word-break:break-all;">{safe_url}</span>
                </p>
              </td>
            </tr>

            <tr>
              <td style="padding:16px 28px;background:#f9fafb;border-top:1px solid #eef2f7;">
                <p style="margin:0;color:#6b7280;font-size:12px;line-height:18px;">
                  Si tú no solicitaste esto, puedes ignorar este mensaje.<br/>
                  Dorians Gym — SenseiFit
                </p>
              </td>
            </tr>

          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[email],
            reply_to=[reply_to] if reply_to else None,
        )
        msg.attach_alternative(html_body, "text/html")
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
            "language": {"code": template_lang},
        },
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