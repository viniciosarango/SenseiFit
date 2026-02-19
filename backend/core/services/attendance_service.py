from django.utils import timezone
from datetime import date


from typing import Optional, Dict

from django.utils import timezone

from core.models import Client, Attendance, Membership
from core.models.plan import Plan


class AttendanceResult:

    def __init__(
        self,
        success: bool,
        attendance_created: bool = False,
        message: str = "",
        reason: str = "",
        attendance: Optional[Attendance] = None,
        extra_data: Optional[Dict] = None,
    ):
        self.success = success
        self.attendance_created = attendance_created
        self.message = message
        self.reason = reason
        self.attendance = attendance
        self.extra_data = extra_data or {}

    def to_dict(self) -> Dict:
        # 1. Construimos el diccionario base
        data = {
            "success": self.success,
            "attendance_created": self.attendance_created,
            "message": self.message,
            "reason": self.reason,
            "attendance_id": self.attendance.id if self.attendance else None,
        }
        # 2. Inyectamos los datos extra (importante para sesiones)
        data.update(self.extra_data)
        return data # 👈 Un solo return al final
    


def register_attendance(
    *,
    client_id: int,
    method: str = "FINGERPRINT",
    source: Optional[str] = None,
) -> AttendanceResult:
    
    # 1. Resolver cliente
    client = _get_client(client_id)
    if not client:
        return AttendanceResult(success=False, message="Cliente no registrado", reason="client_not_found")

    # 2. Obtener membresía activa
    membership = _get_active_membership(client)
    
    # Crear la asistencia ANTES de validar. 
    attendance = Attendance.objects.create(
        client=client,
        #gym=membership.gym if membership else client.gym, # Fallback al gym del cliente
        gym=client.gym,
        membership=membership,
        method=method,
    )
    # 3. Ahora sí, validamos si existe la membresía
    if not membership:
        attendance.message_displayed = "Sin membresía activa" # 👈 Guardamos el error
        attendance.save()
        return AttendanceResult(
            success=False, 
            attendance_created=True, 
            message="No tienes una membresía activa", 
            reason="no_active_membership",
            attendance=attendance
        )

    membership_valid, invalid_reason, invalid_message = _validate_membership(membership)

    if not membership_valid:
        attendance.message_displayed = invalid_message # 👈 Guardamos "Membresía Vencida", etc.
        attendance.save()
        return AttendanceResult(
            success=False,
            attendance_created=True,
            message=invalid_message,
            reason=invalid_reason,
            attendance=attendance
        )

    plan_type = membership.plan.plan_type
    today = timezone.localdate()

    # ======================
    # PLANES POR TIEMPO
    # ======================
    if plan_type in ["TIME", "DAILY"]:
        already_attended_today = Attendance.objects.filter(
            client=client,
            check_in_time__date=today,
        ).exclude(id=attendance.id).exists()

        msg = "¡Bienvenido! Asistencia registrada."
        if already_attended_today:
            msg = "Ya registraste asistencia hoy. ¡Bienvenido de nuevo!"

        attendance.message_displayed = msg # 🎯 AQUÍ
        attendance.save()
        return AttendanceResult(
            success=True,
            attendance_created=True,
            message=msg,
            reason="attendance_recorded",
            attendance=attendance,
        )

    # ======================
    # PLANES POR SESIONES
    # ======================
    elif plan_type == "SESSIONS":
        if membership.sessions_remaining <= 0:
            return AttendanceResult(
                success=False,
                attendance_created=True,
                message="No tienes sesiones disponibles.",
                reason="no_sessions_left",
                attendance=attendance,
                extra_data={"remaining_sessions": 0, "plan_kind": "SESSIONS"}
            )

        membership.sessions_consumed += 1
        membership.save(update_fields=["sessions_consumed"])

        attendance.message_displayed = msg # 🎯 AQUÍ
        attendance.save()
        return AttendanceResult(
            success=True,
            attendance_created=True,
            message="Sesión registrada correctamente.",
            reason="session_consumed",
            attendance=attendance,
            extra_data={
                "remaining_sessions": membership.sessions_remaining,
                "plan_kind": "SESSIONS"
            }
        )

    return AttendanceResult(success=False, message="Tipo de plan no soportado", attendance=attendance)


# =========================================================
# Helpers internos (NO usar fuera de este módulo)
# =========================================================

def _get_client(client_id: int) -> Optional[Client]:
    
    try:
        return Client.objects.select_related("gym").get(id=client_id)
    except Client.DoesNotExist:
        return None


def _get_active_membership(client: Client) -> Optional[Membership]:
    """
    Obtiene la membresía activa del cliente.

    Retorna:
    - Membership activa si existe
    - None si no tiene membresía activa
    """
    return (
        Membership.objects
        .select_related("plan", "gym")
        .filter(
            client=client,
            operational_status="ACTIVE",
        )
        .order_by("-start_date")
        .first()
    )



def _validate_membership(membership: Membership):
    gym = membership.gym
    today = timezone.now().date()

    if membership.operational_status == "BLOCKED":
        return (
            False,
            "membership_blocked",
            "Tu membresía está bloqueada. Consulta en recepción.",
        )

    if membership.operational_status == "INACTIVE":
        return (
            False,
            "membership_inactive",
            "Tu membresía no está activa.",
        )

    if membership.operational_status == "EXPIRED":
        return (
            False,
            "membership_expired",
            "Tu membresía está vencida. Por favor renueva.",
        )

    if membership.balance > 0 and membership.payment_due_date:
        if today > membership.payment_due_date:
            return (
                False,
                "payment_deadline_exceeded",
                f"Plazo de pago vencido. Saldo pendiente: ${membership.balance}.",
            )

    if membership.end_date and membership.end_date < today:
        return (
            False,
            "membership_expired_by_date",
            gym.expiration_alert_message.format(
                name=membership.client.first_name,
                days=0,
            ),
        )

    return True, "", ""



def _handle_time_based_plan(
    *,
    client: Client,
    membership: Membership,
    method: str,
) -> AttendanceResult:
    """
    Maneja planes por tiempo (TIME y DAILY).

    Regla:
    - Solo una asistencia por día
    """

    today = timezone.now().date()

    # ¿Ya existe una asistencia hoy?
    already_attended_today = Attendance.objects.filter(
        client=client,
        gym=membership.gym,
        check_in_time__date=today,
    ).exists()

    if already_attended_today:
        return AttendanceResult(
            success=True,
            attendance_created=False,
            message="Ya registraste tu asistencia hoy. ¡Bienvenido de nuevo!",
            reason="already_attended_today",
        )

    # Crear la asistencia
    attendance = Attendance.objects.create(
        client=client,
        gym=membership.gym,
        membership=membership,
        method=method,
        message_displayed="¡Bienvenido! Asistencia registrada.",
    )

    return AttendanceResult(
        success=True,
        attendance_created=True,
        message=attendance.message_displayed,
        reason="attendance_created",
        attendance=attendance,
    )



def _handle_session_based_plan(
    *,
    client: Client,
    membership: Membership,
    method: str,
) -> AttendanceResult:
    """
    Maneja planes por sesiones (SESSIONS).

    Regla:
    - Cada ingreso crea asistencia
    - Cada asistencia descuenta una sesión
    """

    # 1. Verificar si tiene sesiones disponibles
    total_available_sessions = membership.total_sessions or 0

    used_sessions = Attendance.objects.filter(
        membership=membership
    ).count()

    remaining_sessions = total_available_sessions - used_sessions

    if remaining_sessions <= 0:
        return AttendanceResult(
            success=False,
            attendance_created=False,
            message="No tienes sesiones disponibles. Por favor renueva tu plan.",
            reason="no_remaining_sessions",
        )

    # 2. Crear la asistencia
    attendance = Attendance.objects.create(
        client=client,
        gym=membership.gym,
        membership=membership,
        method=method,
        message_displayed="¡Bienvenido! Sesión registrada.",
    )

    # 3. (Opcional) Aquí puedes enganchar lógica más avanzada luego
    # Ej: notificaciones, alertas, logs

    return AttendanceResult(
        success=True,
        attendance_created=True,
        message=attendance.message_displayed,
        reason="session_attendance_created",
        attendance=attendance,
    )

