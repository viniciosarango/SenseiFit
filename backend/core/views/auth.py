from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import EmailMessage
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.serializers import UserSerializer
from core.services.auth_resolver import resolve_user_by_identifier
from core.services.whatsapp_service import send_whatsapp_template
from core.models.client import Client
from core.models import Company
from django.core.mail import EmailMultiAlternatives
from django.utils.html import escape

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


UserModel = get_user_model()


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)




class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("La contraseña actual es incorrecta.")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        return Response({"detail": "Contraseña actualizada correctamente."})


@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = []  # público

    def post(self, request):
        identifier = (request.data.get("email_or_username") or "").strip()

        ok = Response({"detail": "Si el usuario existe, te enviamos un enlace de recuperación."}, status=200)
        if not identifier:
            return ok

        company = getattr(request, "company", None)
        if not company:
            company = Company.objects.first()   # ✅ fallback para local

        if not company:
            return ok

        user = resolve_user_by_identifier(company, identifier)
        if not user:
            return ok

        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        reset_url = f"{frontend_url}/auth/reset-password?uid={uidb64}&token={token}"

        # 1) si tiene email → email
        if user.email:
            from django.core.mail import EmailMessage
            subject = "Recupera tu contraseña - SenseiFit"
            body = f"""Hola {user.first_name or ''},

Recibimos una solicitud para restablecer tu contraseña.

Abre este enlace para crear una nueva contraseña:
{reset_url}

Si tú no solicitaste esto, ignora este mensaje.

— SenseiFit | Dorians Gym
"""
            if user.email:
                subject = "Recupera tu contraseña - SenseiFit"
                safe_name = escape(user.first_name or "Hola")
                safe_url = escape(reset_url)

                text_body = f"""Hola {user.first_name or ''},

            Recibimos una solicitud para restablecer tu contraseña.

            Abre este enlace para crear una nueva contraseña:
            {reset_url}

            Si tú no solicitaste esto, ignora este mensaje.

            — SenseiFit | Dorians Gym
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
                            <h2 style="margin:0 0 8px 0;color:#111827;font-size:20px;">Recuperar contraseña</h2>
                            <p style="margin:0;color:#374151;font-size:14px;line-height:20px;">
                            Hola {safe_name},<br/>
                            Para crear una nueva contraseña, haz clic en el botón:
                            </p>
                        </td>
                        </tr>

                        <tr>
                        <td align="center" style="padding:18px 28px;">
                            <a href="{safe_url}"
                            style="display:inline-block;background:#2563eb;color:#ffffff;text-decoration:none;
                                    padding:12px 18px;border-radius:10px;font-size:14px;font-weight:bold;">
                            Crear nueva contraseña
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

                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=text_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user.email],
                    reply_to=["soporte@senseifit.app"],
                )
                msg.attach_alternative(html_body, "text/html")
                msg.send(fail_silently=True)

                return ok

        # 2) si NO tiene email → WhatsApp (buscamos teléfono desde Client)
        client = Client.objects.filter(company=company, user=user).first()
        if client and client.phone:
            gym_name = getattr(getattr(client, "gym", None), "name", "") or getattr(company, "name", "Dorians Gym")
            full_name = f"{user.first_name} {user.last_name}".strip() or "Hola"

            send_whatsapp_template(
                to=client.phone,
                template_name="sf_welcome_portal",
                lang="es_EC",
                components=[{
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": full_name},     # {{1}}
                        {"type": "text", "text": gym_name},      # {{2}}
                        {"type": "text", "text": reset_url},     # {{3}}  👈 aquí va reset
                    ],
                }],
            )

        return ok
    

@method_decorator(csrf_exempt, name="dispatch")
class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = []  # público

    def post(self, request):
        uidb64 = (request.data.get("uid") or "").strip()
        token = (request.data.get("token") or "").strip()
        new_password = request.data.get("new_password")

        if not uidb64 or not token or not new_password:
            return Response({"detail": "Datos incompletos."}, status=400)

        # validar password con reglas Django
        try:
            validate_password(new_password)
        except Exception as e:
            # e puede ser ValidationError con lista de mensajes
            return Response({"detail": str(e)}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = UserModel.objects.get(pk=uid)
        except Exception:
            return Response({"detail": "Enlace inválido."}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"detail": "Token inválido o expirado."}, status=400)

        user.set_password(new_password)
        user.must_change_password = False
        user.save(update_fields=["password", "must_change_password"])

        return Response({"detail": "Contraseña actualizada correctamente."}, status=200)