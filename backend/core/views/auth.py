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


class PasswordResetRequestView(APIView):
    permission_classes = []  # público

    def post(self, request):
        email_or_username = (request.data.get("email_or_username") or "").strip().lower()

        # Respuesta neutral (no revelar si existe)
        ok_response = Response(
            {"detail": "Si el usuario existe, te enviamos un enlace de recuperación."},
            status=200
        )

        if not email_or_username:
            return ok_response

        user = (
            UserModel.objects.filter(email__iexact=email_or_username).first()
            or UserModel.objects.filter(username__iexact=email_or_username).first()
        )

        if not user or not user.email:
            return ok_response

        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        reset_url = f"{frontend_url}/auth/reset-password?uid={uidb64}&token={token}"

        subject = "Recupera tu contraseña - SenseiFit"
        body = f"""Hola {user.first_name or ''},

Recibimos una solicitud para restablecer tu contraseña.

Abre este enlace para crear una nueva contraseña:
{reset_url}

Si tú no solicitaste esto, ignora este mensaje.

— SenseiFit
"""

        try:
            EmailMessage(
                subject=subject,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
                reply_to=["soporte@senseifit.app"],
            ).send(fail_silently=True)
        except Exception:
            pass

        return ok_response
    

class PasswordResetConfirmView(APIView):
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