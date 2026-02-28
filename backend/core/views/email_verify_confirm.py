from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import EmailVerificationToken


class VerifyEmailTokenView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get("token")
        if not token_str:
            return Response({"detail": "Token requerido."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            evt = EmailVerificationToken.objects.select_related("contact_point").get(token=token_str)
        except EmailVerificationToken.DoesNotExist:
            return Response({"detail": "Token inválido."}, status=status.HTTP_400_BAD_REQUEST)

        if evt.is_used:
            return Response({"detail": "Este token ya fue usado."}, status=status.HTTP_400_BAD_REQUEST)

        if evt.is_expired:
            return Response({"detail": "Este token expiró. Solicita uno nuevo."}, status=status.HTTP_400_BAD_REQUEST)

        cp = evt.contact_point
        cp.is_verified = True
        cp.save(update_fields=["is_verified"])

        evt.mark_used()

        return Response({"detail": "Email verificado correctamente."}, status=status.HTTP_200_OK)