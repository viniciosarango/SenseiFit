from django.core.mail import send_mail
from django.conf import settings


def send_client_credentials_email(*, email, username, temp_password):
    """
    Envío profesional de credenciales iniciales.
    """

    if not email:
        return  # No hacemos nada si no hay email

    subject = "Bienvenido a Dorian's Gym 🏋️‍♂️"

    message = f"""
Hola,

Tu cuenta ha sido creada correctamente.

Usuario: {username}
Contraseña temporal: {temp_password}

Por seguridad, cambia tu contraseña en el primer ingreso.

Nos vemos en el gym 💪
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )
