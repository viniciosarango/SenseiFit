from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from core.models import ContactPoint, EmailVerificationToken
from core.services.notification_service import send_email_verification_link


class SendEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Solo CLIENT puede pedir verificación desde portal
        if user.role != user.Roles.CLIENT:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        client = getattr(user, "client_profile", None)
        if not client:
            return Response({"detail": "Cliente no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        cp = ContactPoint.objects.filter(
            company=client.company,
            client=client,
            type=ContactPoint.Types.EMAIL,
            is_primary=True,
        ).first()

        if not cp:
            return Response({"detail": "No tienes un email principal configurado."}, status=status.HTTP_400_BAD_REQUEST)

        if cp.is_verified:
            return Response({"detail": "Este email ya está verificado."}, status=status.HTTP_200_OK)

        token = EmailVerificationToken.objects.create(
            contact_point=cp,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")
        verify_url = f"{frontend_url}/verificar-email?token={token.token}" if frontend_url else None

        send_email_verification_link(
            email=cp.value,
            full_name=client.full_name,
            verify_url=verify_url,
            reply_to=client.company.support_email
        )

        return Response({"detail": "Te enviamos un correo para verificar tu email."}, status=status.HTTP_200_OK)