from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from core.models import Membership, Payment, Plan, PaymentMethod
from django.db import IntegrityError

from django.core.exceptions import ValidationError
from core.utils.hikvision import sync_hikvision_async


class MembershipError(Exception):
    pass

MONEY_Q = Decimal("0.01")

def money(v):
    return Decimal(str(v or 0)).quantize(MONEY_Q, rounding=ROUND_HALF_UP)


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
    sale_type="CASH",
    payment_grace_days_override=None,
):
    # 1) Obtener Plan
    try:
        plan = Plan.objects.get(id=plan_id)
    except Plan.DoesNotExist:
        raise MembershipError("El plan seleccionado no existe.")

    if plan.gym_id != gym.id:
        raise MembershipError("El plan no pertenece a este gimnasio.")

    today = timezone.localdate()
    start_date = requested_start_date or today

    # ✅ Guardamos el pago inicial aparte (NO se escribe en membership directo)
    initial_paid = money(paid_amount)

    # 2) Buscar membresía actualmente ACTIVA (Seguridad del búnker)
    active_mem = Membership.objects.filter(
        client=client,
        gym=gym,
        operational_status="ACTIVE",
        plan__plan_type=plan.plan_type
    ).first()

    # 3) Lógica de Fila de Renovación
    last_mem = None
    if plan.plan_type == 'TIME':
        last_mem = Membership.objects.filter(
            client=client,
            gym=gym,
            operational_status__in=["ACTIVE", "SCHEDULED"]
        ).order_by("-end_date").first()

    # 4) DETERMINACIÓN DE ESTADO Y FECHAS
    if force_operational_status:
        if force_operational_status == "ACTIVE" and active_mem:
            raise MembershipError(
                f"El cliente ya tiene una membresía activa (ID: {active_mem.id}). "
                "No puedes forzar otra como ACTIVA simultáneamente."
            )
        operational_status = force_operational_status
        action = "INSCRIPTION"
        start_date = start_date

    elif last_mem and last_mem.end_date:
        action = "RENEWAL"
        operational_status = "SCHEDULED"
        start_date = last_mem.end_date + timedelta(days=1)

    else:
        action = "INSCRIPTION"
        operational_status = "ACTIVE" if start_date <= today else "SCHEDULED"

        if operational_status == "ACTIVE" and active_mem:
            operational_status = "SCHEDULED"

    # 5) Calcular fecha de fin
    end_date = start_date + timedelta(days=plan.duration_days - 1)

    discount_percent = discount_percent or 0
    enrollment_fee = enrollment_fee or 0

    original_price = money(plan.price)
    discount_percent_applied = money(discount_percent)
    enrollment_fee_applied = money(enrollment_fee)
    
    
    membership = Membership.objects.create(
        client=client,
        gym=gym,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        action=action,
        original_price=original_price,
        discount_percent_applied=discount_percent_applied,
        enrollment_fee_applied=enrollment_fee_applied,
        paid_amount=Decimal("0.00"),
        operational_status=operational_status,
        created_by=created_by,
        notes=notes,sale_type=sale_type,
        payment_grace_days_override=payment_grace_days_override,

    )

    # 7) Pago inicial (si existe)
    if initial_paid > 0:
        if not payment_method_id:
            raise MembershipError("Debe seleccionar método de pago para registrar el pago inicial.")

        from core.services.payments import register_payment

        register_payment(
            membership_id=membership.id,
            amount=initial_paid,
            payment_method_id=payment_method_id,
            notes="Pago inicial inscripción",
            created_by=created_by
        )

    if membership.start_date and membership.end_date:
        sync_hikvision_async(membership)

    membership.refresh_from_db()

    

    # --------------------------------------------------------
    # Reordenar cola TIME si se forzó ACTIVE
    # --------------------------------------------------------
    if force_operational_status == "ACTIVE" and plan.plan_type == "TIME":
        scheduled_times = Membership.objects.filter(
            client=client,
            gym=gym,
            plan__plan_type="TIME",
            operational_status="SCHEDULED"
        ).order_by("start_date")

        last_end_date = membership.end_date

        for m in scheduled_times:
            duration = m.plan.duration_days

            new_start = last_end_date + timedelta(days=1)
            new_end = new_start + timedelta(days=duration - 1)

            m.start_date = new_start
            m.end_date = new_end
            m.save(update_fields=["start_date", "end_date"])

            last_end_date = new_end

    # Plazo de pago si quedó deuda
    if membership.balance > 0 and not membership.payment_due_date:
        grace_days = membership.payment_grace_days_override or membership.gym.default_payment_grace_days
        base_date = membership.start_date if membership.operational_status == "SCHEDULED" and membership.start_date else today
        membership.payment_due_date = base_date + timedelta(days=grace_days)
        membership.save(update_fields=['payment_due_date'])

    # ✅ MAKE: evento membership.created
    try:
        from core.services.integrations.make_webhook_service import send_make_event

        payment_method = None
        if payment_method_id:
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id)
            except PaymentMethod.DoesNotExist:
                payment_method = None

        send_make_event(
            event="membership.created",
            data={

                "payment_method": {
                    "id": getattr(payment_method, "id", None),
                    "name": getattr(payment_method, "name", None),
                } if payment_method else None,

                "initial_payment": {
                    "amount": float(initial_paid or 0),
                    "method_id": getattr(payment_method, "id", None),
                    "method_name": getattr(payment_method, "name", None),
                } if initial_paid > 0 else None,


                "membership": {
                    "id": membership.id,
                    "action": getattr(membership, "action", None),
                    "operational_status": getattr(membership, "operational_status", None),
                    "financial_status": getattr(membership, "financial_status", None),
                    # "start_date": str(getattr(membership, "start_date", "") or ""),
                    # "end_date": str(getattr(membership, "end_date", "") or ""),
                    "start_date": str(membership.start_date) if getattr(membership, "start_date", None) else None,
                    "end_date": str(membership.end_date) if getattr(membership, "end_date", None) else None,
                    "original_price": float(getattr(membership, "original_price", 0) or 0),
                    
                    #"discount_percent_applied": float(getattr(membership, "discount_percent_applied", 0) or 0),
                    "discount_percent_applied": float(membership.discount_percent_applied or 0),

                    #"enrollment_fee_applied": float(getattr(membership, "enrollment_fee_applied", 0) or 0),
                    "enrollment_fee_applied": float(membership.enrollment_fee_applied or 0),
                    
                    "total_amount": float(getattr(membership, "total_amount", 0) or 0),
                    "paid_amount": float(getattr(membership, "paid_amount", 0) or 0),
                    "balance": float(getattr(membership, "balance", 0) or 0),
                    #"payment_due_date": str(getattr(membership, "payment_due_date", "") or ""),
                    "payment_due_date": str(membership.payment_due_date) if getattr(membership, "payment_due_date", None) else None,
                    "sale_type": getattr(membership, "sale_type", None) or None,
                    "notes": getattr(membership, "notes", "") or "",
                },
                "client": {
                    "id": client.id,
                    "full_name": f"{client.first_name} {client.last_name}".strip(),
                    "email": getattr(client, "email", None),
                    "phone": getattr(client, "phone", None),
                    "id_number": getattr(client, "id_number", None),
                },
                "gym": {
                    "id": gym.id,
                    "name": getattr(gym, "name", ""),
                },
                "plan": {
                    "id": plan.id,
                    "name": getattr(plan, "name", ""),
                    "plan_type": getattr(plan, "plan_type", ""),
                    #"duration_days": getattr(plan, "duration_days", None),
                    "duration_days": int(getattr(plan, "duration_days", 0) or 0),
                    "price": float(getattr(plan, "price", 0) or 0),
                },
                "company": {
                    "id": getattr(getattr(gym, "company", None), "id", None),
                    "name": getattr(getattr(gym, "company", None), "name", None),
                },
                "created_by": {
                    "id": getattr(created_by, "id", None),
                    "username": getattr(created_by, "username", None),
                },
            },
        )
    except Exception as e:
        print("MAKE membership.created error:", str(e), flush=True)


    

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



@transaction.atomic
def activate_membership_now(*, membership: Membership, activated_by):

    today = timezone.localdate()

    if membership.operational_status != "SCHEDULED":
        raise MembershipError("Solo se pueden activar membresías programadas.")

    # Verificar que no exista otra ACTIVE
    existing_active = Membership.objects.filter(
        client=membership.client,
        gym=membership.gym,
        operational_status="ACTIVE"
    ).exists()

    if existing_active:
        raise MembershipError("Ya existe una membresía activa para este cliente.")

    # Recalcular fechas
    membership.start_date = today
    membership.end_date = today + timedelta(days=membership.plan.duration_days - 1)
    membership.operational_status = "ACTIVE"

    membership.save(update_fields=[
        "start_date",
        "end_date",
        "operational_status"
    ])

    # Reordenar futuras SCHEDULED
    next_start = membership.end_date + timedelta(days=1)

    future_queue = (
        Membership.objects
        .filter(
            client=membership.client,
            gym=membership.gym,
            operational_status="SCHEDULED",
            start_date__gt=membership.start_date
        )
        .order_by("start_date")
    )

    for future in future_queue:
        future.start_date = next_start
        future.end_date = next_start + timedelta(days=future.plan.duration_days - 1)
        future.save(update_fields=["start_date", "end_date"])
        next_start = future.end_date + timedelta(days=1)

    sync_hikvision_async(membership)

    return membership



@transaction.atomic
def freeze_membership_service(*, membership: Membership, requested_by, pin: str):

    today = timezone.localdate()

    # 🔒 Validar PIN primero
    from django.conf import settings
    expected_pin = getattr(settings, "CANCEL_PIN", None)

    if not expected_pin:
        raise MembershipError("No hay PIN configurado.")

    if str(pin) != str(expected_pin):
        raise MembershipError("PIN incorrecto. No autorizado.")

    # 🧠 Reglas de negocio
    if membership.plan.plan_type != "TIME":
        raise MembershipError("Solo los planes por tiempo pueden congelarse.")

    if membership.operational_status != "ACTIVE":
        raise MembershipError("Solo una membresía activa puede congelarse.")
    
    if membership.balance > 0:
        raise MembershipError(
            f"No se puede congelar. Tiene saldo pendiente de ${membership.balance}."
        )

    if membership.total_freeze_days >= 30:
        raise MembershipError("Ya alcanzó el máximo de 30 días de congelamiento.")

    # 🎯 Aplicar congelamiento
    membership.operational_status = "FROZEN"
    membership.freeze_start_date = today
    membership.freeze_requested_by = requested_by
    membership.freeze_timestamp = timezone.now()

    membership.save(update_fields=[
        "operational_status",
        "freeze_start_date",
        "freeze_requested_by",
        "freeze_timestamp"
    ])

    return membership



@transaction.atomic
def unfreeze_membership_service(*, membership: Membership, requested_by, pin: str):

    from django.conf import settings
    expected_pin = getattr(settings, "CANCEL_PIN", None)

    if not expected_pin:
        raise MembershipError("No hay PIN configurado.")

    if str(pin) != str(expected_pin):
        raise MembershipError("PIN incorrecto. No autorizado.")

    today = timezone.localdate()

    if membership.operational_status != "FROZEN":
        raise MembershipError("La membresía no está congelada.")

    if not membership.freeze_start_date:
        raise MembershipError("Error interno: fecha de congelamiento no encontrada.")

    frozen_days = (today - membership.freeze_start_date).days

    if frozen_days <= 0:
        raise MembershipError("No se puede descongelar el mismo día.")

    if membership.total_freeze_days + frozen_days >= 30:
        membership.operational_status = "INACTIVE"
        membership.freeze_start_date = None
        membership.total_freeze_days = 30
        membership.save(update_fields=[
            "operational_status",   
            "freeze_start_date",
            "total_freeze_days"
        ])
        raise MembershipError("Límite de 30 días alcanzado. La membresía quedó inactiva.")

    membership.end_date += timedelta(days=frozen_days)
    membership.total_freeze_days += frozen_days
    membership.operational_status = "ACTIVE"
    membership.freeze_start_date = None
    membership.unfreeze_requested_by = requested_by
    membership.unfreeze_timestamp = timezone.now()

    membership.save(update_fields=[
        "end_date",
        "total_freeze_days",
        "operational_status",
        "freeze_start_date",
        "unfreeze_requested_by",
        "unfreeze_timestamp"
    ])

    from core.utils.hikvision import sync_hikvision_async
    sync_hikvision_async(membership)

    return membership