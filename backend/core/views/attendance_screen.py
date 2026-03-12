from django.conf import settings
from django.utils import timezone
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from core.models.attendance import HikvisionAccessEvent


@api_view(["GET"])
@authentication_classes([])
@permission_classes([])
def last_attendance(request):

    screen_key = request.headers.get("X-SCREEN-KEY")
    is_screen_mode = (
        bool(getattr(settings, "ATTENDANCE_SCREEN_KEY", ""))
        and screen_key == settings.ATTENDANCE_SCREEN_KEY
    )

    user = request.user

    if not is_screen_mode:
        if not user.is_authenticated:
            return Response({"has_data": False}, status=401)

        if not user.is_superuser and not user.gym:
            return Response({"has_data": False}, status=403)

    queryset = HikvisionAccessEvent.objects.select_related(
        "client",
        "membership__plan"
    ).filter(processing_status="PROCESSED")

    if not is_screen_mode and not user.is_superuser:
        queryset = queryset.filter(gym=user.gym)

    attendance = queryset.order_by("-received_at").first()

    if not attendance:
        return Response({"has_data": False})

    membership = getattr(attendance, "membership", None)
    gym = attendance.gym or (membership.gym if membership else None)
    client = attendance.client

    # --- 1. DATOS BÁSICOS ---
    start_date = membership.start_date if membership else None
    end_date = membership.end_date if membership else None
    days_left = None

    # --- 2. LÓGICA DE COLOR ---
    color = "red"

    if membership:
        today = timezone.localdate()

        if end_date:
            days_left = (end_date - today).days

        if membership.operational_status != "ACTIVE":
            color = "red"
        else:
            plan_type = membership.plan.plan_type

            if plan_type == "SESSIONS":
                color = "green" if membership.sessions_remaining > 0 else "red"
            else:
                if days_left is not None:
                    if days_left < 0:
                        color = "red"
                    elif days_left == 0:
                        color = "orange"
                    elif days_left <= 3:
                        color = "yellow"
                    else:
                        color = "green"

    # --- 3. URL DE FOTO ---
    photo_url = None
    if hasattr(client, "photo") and client.photo:
        try:
            photo_url = client.photo.url
        except Exception:
            photo_url = None

    # --- 4. RESPUESTA ---
    return Response({
        "has_data": True,
        "access_event_id": attendance.id,
        "client": f"{client.first_name} {client.last_name}".strip(),
        "plan": membership.plan.name if membership and membership.plan else "SIN MEMBRESÍA",
        "message": attendance.notes or (
            "Acceso permitido. ¡Bienvenido!"
            if attendance.access_result == "granted"
            else "Acceso denegado. Revisar membresía o estado del cliente."
        ),
        "access_result": attendance.access_result,
        "direction": attendance.direction,
        "check_in_time": attendance.occurred_at or attendance.received_at,
        "start_date": start_date,
        "end_date": end_date,
        "days_left": days_left,
        "color": color,
        "photo_url": photo_url,
        "device_id": attendance.device_id,
        "device_name": attendance.device_name,
        "hikvision_person_id": attendance.hikvision_person_id,
        "processing_status": attendance.processing_status,
        "source": attendance.raw_payload.get("source"),
        "plan_kind": membership.plan.plan_type if membership else "TIME",
        "remaining_sessions": membership.sessions_remaining if membership else 0,
        "tv_idle_mode": gym.tv_idle_mode if gym else "text",
        "tv_idle_title": gym.tv_idle_title if gym else "Dorians Gym",
        "tv_idle_subtitle": gym.tv_idle_subtitle if gym else "¡Transforma tu vida!",
        "tv_idle_message": gym.tv_idle_message if gym else "Esperando próximo acceso...",
        "tv_idle_image_url": gym.tv_idle_image_url if gym else "",
        "tv_idle_video_url": gym.tv_idle_video_url if gym else "",
        "tv_idle_youtube_url": gym.tv_idle_youtube_url if gym else "",
        "tv_event_display_seconds": gym.tv_event_display_seconds if gym else 10,
    })