from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from core.services.attendance_service import register_attendance
from core.models import Client


@method_decorator(csrf_exempt, name='dispatch')
class AttendanceWebhookView(APIView):
    """
    Endpoint seguro para registrar asistencias desde dispositivos externos.
    Autenticación por API_KEY.
    """

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        # 🔐 1. Validación API KEY
        api_key = request.headers.get("X-API-KEY")

        if api_key != settings.ATTENDANCE_WEBHOOK_KEY:
            return Response(
                {"success": False, "reason": "invalid_api_key"},
                status=status.HTTP_403_FORBIDDEN
            )

        hikvision_id = request.data.get("hikvision_id")
        method = request.data.get("method", "FINGERPRINT")
        source = request.data.get("source")

        # 2. Validación mínima
        if not hikvision_id:
            return Response(
                {
                    "success": False,
                    "reason": "missing_hikvision_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Resolver cliente
        try:
            client = Client.objects.select_related("gym").get(
                hikvision_id=hikvision_id
            )
        except Client.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "reason": "client_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        # 4. Registrar asistencia
        result = register_attendance(
            client_id=client.id,
            method=method,
            source=source,
        )

        http_status = (
            status.HTTP_200_OK if result.success
            else status.HTTP_403_FORBIDDEN
        )

        return Response(result.to_dict(), status=http_status)
