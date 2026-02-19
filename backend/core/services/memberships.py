from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from core.models import Membership, Payment, Plan
from django.db import IntegrityError

from django.core.exceptions import ValidationError
from core.utils.hikvision import sync_hikvision_async


class MembershipError(Exception):
    pass

@transaction.atomic
def create_membership_service(
    *,
    client,
    gym,
    plan_id,
    requested_start_date=None,
    discount_percent=0,
    enrollment_fee=0,
    paid_amount=0,
    payment_method_id=None,
    created_by=None,
    notes="",
    force_operational_status=None,
):
    # 1) Obtener Plan
    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        raise MembershipError("El plan seleccionado no existe.")

    today = timezone.localdate()
    start_date = requested_start_date or today

    # 2) Buscar membresía actualmente ACTIVA (Seguridad del búnker)
    active_mem = Membership.objects.filter(
        client=client,
        gym=gym,
        operational_status="ACTIVE"
    ).first()

    # 3) Lógica de Fila de Renovación
    # 🎯 Solo buscamos la "última" si NO es un plan de sesiones (Ticketera)
    last_mem = None
    if plan.plan_type not in ['SESSIONS', 'DAILY']:
        last_mem = Membership.objects.filter(
            client=client,
            gym=gym,
            operational_status__in=["ACTIVE", "SCHEDULED"]
        ).order_by("-end_date").first()

    # 4) DETERMINACIÓN DE ESTADO Y FECHAS
    
    # CASO A: El usuario envía un estado forzado (ej: desde el Admin o un switch)
    if force_operational_status:
        # 🛡️ Candado: No permitimos dos ACTIVAS a la vez
        if force_operational_status == "ACTIVE" and active_mem:
            raise MembershipError(
                f"El cliente ya tiene una membresía activa (ID: {active_mem.id}). "
                "No puedes forzar otra como ACTIVA simultáneamente."
            )
        operational_status = force_operational_status
        action = "INSCRIPTION" 
        start_date = start_date

    # CASO B: Renovación Automática (Cola de espera para planes de tiempo)
    elif last_mem and last_mem.end_date:
        action = "RENEWAL"
        operational_status = "SCHEDULED"
        # La nueva empieza un día después de que venza la última en cola
        start_date = last_mem.end_date + timedelta(days=1)
        
    # CASO C: Inscripción Nueva o Ticketera (Sesiones)
    else:
        action = "INSCRIPTION"
        # Se activa hoy si la fecha coincide, o se programa si es a futuro
        operational_status = "ACTIVE" if start_date <= today else "SCHEDULED"
        
        # 🛡️ Candado de respaldo: Si le toca ser ACTIVE pero ya hay una...
        if operational_status == "ACTIVE" and active_mem:
            # La mandamos a la fila como PROGRAMADA para evitar el choque
            operational_status = "SCHEDULED"

    # 5) Calcular fecha de fin basada en la lógica de arriba
    end_date = start_date + timedelta(days=plan.duration_days - 1)

    # 6) Crear membresía
    membership = Membership.objects.create(
        client=client,
        gym=gym,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        action=action,
        original_price=plan.price,
        discount_percent_applied=Decimal(str(discount_percent)),
        enrollment_fee_applied=Decimal(str(enrollment_fee)),
        paid_amount=Decimal(str(paid_amount or 0)),
        operational_status=operational_status,
        created_by=created_by,
        notes=notes,
    )

    # 7) Pago inicial y Sincronización
    if paid_amount and payment_method_id:
        Payment.objects.create(
            membership=membership,
            gym=gym,
            client=client,
            amount=paid_amount,
            payment_method_id=payment_method_id,
            notes=f"Pago inicial membresía {membership.id}",
        )

    if membership.start_date and membership.end_date:
        sync_hikvision_async(membership)

    membership.refresh_from_db()

    # Plazo de pago si quedó deuda
    if membership.balance > 0 and not membership.payment_due_date:
        membership.payment_due_date = today + timedelta(days=7)
        membership.save(update_fields=['payment_due_date'])

    return membership


@transaction.atomic
def cancel_membership_service(*, membership, requested_by, pin: str, reason: str = ""):
    # 1) Validar estados permitidos
    if membership.operational_status not in ["ACTIVE", "SCHEDULED"]:
        raise MembershipError("Solo se puede cancelar una membresía ACTIVA o PROGRAMADA.")

    # 2) Validar PIN (provisional: por settings)
    from django.conf import settings
    expected_pin = getattr(settings, "CANCEL_PIN", None)
    if not expected_pin:
        raise MembershipError("No hay PIN configurado en settings (CANCEL_PIN).")
    if str(pin) != str(expected_pin):
        raise MembershipError("PIN incorrecto. No autorizado para cancelar.")

    # 3) Cancelar
    membership.operational_status = "CANCELLED"
    # opcional: guardar reason en notes sin romper nada
    if reason:
        membership.notes = f"{membership.notes or ''} | CANCELLED: {reason}".strip()
    membership.save(update_fields=["operational_status", "notes"])

    # 4) (Opcional) sync hikvision para cortar acceso
    sync_hikvision_async(membership)

    return membership