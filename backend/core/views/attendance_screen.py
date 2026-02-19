from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from core.models import Attendance


@api_view(["GET"])
def last_attendance(request):

    user = request.user

    if not user.is_authenticated:
        return Response({"has_data": False}, status=401)

    if not user.is_superuser and not user.gym:
        return Response({"has_data": False}, status=403)

    # 🔒 Filtrado multi-tenant
    queryset = Attendance.objects.select_related(
        "client",
        "membership__plan"
    )

    if not user.is_superuser:
        queryset = queryset.filter(gym=user.gym)

    attendance = queryset.order_by("-check_in_time").first()

    if not attendance:
        return Response({"has_data": False})

    membership = getattr(attendance, "membership", None)
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
        "attendance_id": attendance.id,
        "client": f"{client.first_name} {client.last_name}".strip(),
        "plan": membership.plan.name if membership and membership.plan else "SIN MEMBRESÍA",
        "message": attendance.message_displayed or "¡Bienvenido!",
        "check_in_time": attendance.check_in_time,
        "start_date": start_date,
        "end_date": end_date,
        "days_left": days_left,
        "color": color,
        "photo_url": photo_url,
        "plan_kind": membership.plan.plan_type if membership else "TIME",
        "remaining_sessions": membership.sessions_remaining if membership else 0,
    })
