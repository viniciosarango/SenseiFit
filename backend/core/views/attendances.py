from django.conf import settings
from django.db import IntegrityError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from core.services.attendance_service import register_attendance
from core.services.hikvision_event_service import build_hikvision_event_fingerprint
from core.models import Client
from core.models.attendance import HikvisionAccessEvent


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
        # api_key = request.headers.get("X-API-KEY")

        # if api_key != settings.ATTENDANCE_WEBHOOK_KEY:
        #     return Response(
        #         {"success": False, "reason": "invalid_api_key"},
        #         status=status.HTTP_403_FORBIDDEN
        #     )

        # 🔐 1. Validación API KEY
        api_key = (
            request.headers.get("X-API-KEY")
            or request.query_params.get("api_key")
        )

        if api_key != settings.ATTENDANCE_WEBHOOK_KEY:
            return Response(
                {"success": False, "reason": "invalid_api_key"},
                status=status.HTTP_403_FORBIDDEN
            )

        hikvision_id = request.data.get("hikvision_id")
        method = request.data.get("method", "FINGERPRINT")
        source = request.data.get("source")
        device_id = request.data.get("device_id")
        device_name = request.data.get("device_name")
        occurred_at = request.data.get("occurred_at")
        direction = request.data.get("direction", "ENTRY")
        event_type = request.data.get("event_type", "ACCESS")
        external_event_id = request.data.get("external_event_id")

        source_ip = request.META.get("HTTP_X_FORWARDED_FOR")
        if source_ip:
            source_ip = source_ip.split(",")[0].strip()
        else:
            source_ip = request.META.get("REMOTE_ADDR")

        raw_payload = {
            **dict(request.data),
            "source": source,
        }        

        # 2. Validación mínima
        if not hikvision_id:
            return Response(
                {
                    "success": False,
                    "reason": "missing_hikvision_id",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 3. Construir fingerprint e intentar guardar evento crudo
        event_fingerprint = build_hikvision_event_fingerprint(
            hikvision_person_id=hikvision_id,
            device_id=device_id,
            occurred_at=occurred_at,
            direction=direction,
            event_type=event_type,
            raw_payload=raw_payload,
        )

        try:
            access_event = HikvisionAccessEvent.objects.create(
                external_event_id=external_event_id,
                event_fingerprint=event_fingerprint,
                hikvision_person_id=hikvision_id,
                device_id=device_id,
                device_name=device_name,
                direction=direction if direction in ["ENTRY", "EXIT", "UNKNOWN"] else "UNKNOWN",
                method=method,
                occurred_at=occurred_at or None,
                source_ip=source_ip,
                raw_payload=raw_payload,
                processing_status="PENDING",
            )            
        except IntegrityError:
            return Response(
                {
                    "success": True,
                    "reason": "duplicate_event_ignored",
                    "message": "Evento duplicado ignorado.",
                },
                status=status.HTTP_200_OK,
            )

        # 4. Resolver cliente
        try:
            client = Client.objects.get(hikvision_id=hikvision_id)
        
        except Client.DoesNotExist:
            access_event.processing_status = "FAILED"
            access_event.processing_error = "client_not_found"
            access_event.access_result = "unknown_person"
            access_event.save(
                update_fields=[
                    "processing_status",
                    "processing_error",
                    "access_result",
                ]
            )

            return Response(
                {
                    "success": False,
                    "reason": "client_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )        

        # Vincular cliente al evento crudo
        access_event.client = client
        access_event.save(update_fields=["client"])

        # 5. Registrar asistencia con el flujo actual
        result = register_attendance(
            client_id=client.id,
            method=method,
            source=source,
        )

        # Reflejar resultado en el evento crudo
        access_event.processing_status = "PROCESSED"
        access_event.processing_error = ""        

        if result.attendance:
            access_event.membership = result.attendance.membership
            access_event.gym = result.attendance.membership.gym if result.attendance.membership else None
            access_event.access_result = "granted" if result.success else "denied"
            access_event.notes = result.message or ""
            access_event.save(
                update_fields=[
                    "processing_status",
                    "processing_error",
                    "membership",
                    "gym",
                    "access_result",
                    "notes",
                ]
            )         

        else:
            access_event.access_result = "granted" if result.success else "denied"
            access_event.save(
                update_fields=[
                    "processing_status",
                    "processing_error",
                    "access_result",
                ]
            )

        http_status = (
            status.HTTP_200_OK if result.success
            else status.HTTP_403_FORBIDDEN
        )

        return Response(result.to_dict(), status=http_status)
