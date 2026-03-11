from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from core.models import Membership, Payment, Plan, PaymentMethod
from django.db import IntegrityError

from django.core.exceptions import ValidationError
from core.utils.hikvision import sync_hikvision_async, revoke_hikvision_access


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
    payment_due_date=None,
    credit_days=None,
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

    initial_paid = money(paid_amount)
    if sale_type not in {"CASH", "CREDIT"}:
        raise MembershipError("Tipo de venta inválido.")

    active_mem = Membership.objects.filter(
        client=client,
        gym=gym,
        operational_status="ACTIVE",
        plan__plan_type=plan.plan_type
    ).first()


    last_mem = None
    if plan.plan_type == 'TIME':
        last_mem = Membership.objects.filter(
            client=client,
            gym=gym,
            plan__plan_type=plan.plan_type,
            operational_status__in=["ACTIVE", "SCHEDULED", "FROZEN"]
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

    renovation_date = end_date + timedelta(days=1)

    discount_percent = discount_percent or 0
    enrollment_fee = enrollment_fee or 0

    original_price = money(plan.price)
    discount_percent_applied = money(discount_percent)
    enrollment_fee_applied = money(enrollment_fee)

    discount_amount = (original_price * discount_percent_applied / Decimal("100")).quantize(MONEY_Q, rounding=ROUND_HALF_UP)
    final_price = (original_price - discount_amount).quantize(MONEY_Q, rounding=ROUND_HALF_UP)
    total_amount = (final_price + enrollment_fee_applied).quantize(MONEY_Q, rounding=ROUND_HALF_UP)

    if sale_type == "CASH":
        if initial_paid != total_amount:
            raise MembershipError("Una venta CASH exige pago total exacto.")
        resolved_payment_due_date = None

    elif sale_type == "CREDIT":
        if initial_paid > total_amount:
            raise MembershipError("El abono inicial no puede exceder el total de la membresía.")

        if initial_paid < total_amount:
            if payment_due_date and payment_due_date <= today:
                raise MembershipError("La fecha límite de pago debe ser posterior a hoy.")            
            if payment_due_date:
                resolved_payment_due_date = payment_due_date
            elif credit_days is not None:
                if int(credit_days) <= 0:
                    raise MembershipError("Los días de crédito deben ser mayores a 0.")
                resolved_payment_due_date = today + timedelta(days=int(credit_days))            
            else:
                resolved_payment_due_date = today + timedelta(days=gym.default_payment_grace_days)
        else:
            resolved_payment_due_date = None
    
    membership = Membership.objects.create(
        client=client,
        gym=gym,
        plan=plan,
        start_date=start_date,
        end_date=end_date,
        renovation_date=renovation_date,
        action=action,
        original_price=original_price,
        discount_percent_applied=discount_percent_applied,
        enrollment_fee_applied=enrollment_fee_applied,
        total_amount=total_amount,
        paid_amount=Decimal("0.00"),
        operational_status=operational_status,
        created_by=created_by,
        notes=notes,
        sale_type=sale_type,
        payment_due_date=resolved_payment_due_date,
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

    membership.hikvision_synced = False
    membership.hikvision_message = ""
    membership.hikvision_attempted = False

    if membership.client and membership.client.hikvision_id and membership.start_date and membership.end_date:
        membership.hikvision_attempted = True
        try:
            ok, message = sync_hikvision_async(membership)
            membership.hikvision_synced = bool(ok)
            membership.hikvision_message = message or ""
        except Exception as e:
            membership.hikvision_synced = False
            membership.hikvision_message = str(e)
            print("Hikvision sync error:", str(e), flush=True)

    membership.refresh_from_db()


    

    # --------------------------------------------------------
    # Reordenar cola TIME si se forzó ACTIVE
    # --------------------------------------------------------
    if force_operational_status == "ACTIVE" and plan.plan_type == "TIME":
        scheduled_times = Membership.objects.filter(
            client=client,
            gym=gym,
            plan__plan_type=plan.plan_type,
            operational_status="SCHEDULED"
        ).order_by("start_date")

        last_end_date = membership.end_date

        for m in scheduled_times:
            duration = m.plan.duration_days

            new_start = last_end_date + timedelta(days=1)
            new_end = new_start + timedelta(days=duration - 1)

            m.start_date = new_start
            m.end_date = new_end
            m.save(update_fields=["start_date", "end_date", "renovation_date"])

            last_end_date = new_end

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
                    "renovation_date": str(getattr(membership, "renovation_date", None)) if getattr(membership, "renovation_date", None) else None,

                    "original_price": float(getattr(membership, "original_price", 0) or 0),
                    
                    #"discount_percent_applied": float(getattr(membership, "discount_percent_applied", 0) or 0),
                    "discount_percent_applied": float(membership.discount_percent_applied or 0),

                    #"enrollment_fee_applied": float(getattr(membership, "enrollment_fee_applied", 0) or 0),
                    "enrollment_fee_applied": float(membership.enrollment_fee_applied or 0),
                    
                    "total_amount": float(getattr(membership, "total_amount", 0) or 0),
                    "paid_amount": float(getattr(membership, "paid_amount", 0) or 0),
                    "balance": float(getattr(membership, "balance", 0) or 0),
                    
                    "sale_type": getattr(membership, "sale_type", None) or None,
                    "payment_due_date": str(membership.payment_due_date) if membership.payment_due_date else None,
                    "notes": getattr(membership, "notes", "") or "",

                    "courtesy_qty": int(getattr(membership, "courtesy_qty", 0) or 0),
                    "courtesy_used": int(getattr(membership, "courtesy_used", 0) or 0),
                    "courtesy_balance": int((getattr(membership, "courtesy_qty", 0) or 0) - (getattr(membership, "courtesy_used", 0) or 0)),

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

    # 3) cancelar
    membership.operational_status = "CANCELLED"
    membership.payment_due_date = None

    if reason:
        membership.notes = f"{membership.notes or ''} | CANCELLED: {reason}".strip()

    membership.save(update_fields=["operational_status", "payment_due_date", "notes"])    

    # 4) (Opcional) sync hikvision para cortar acceso
    revoke_hikvision_access(membership)

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
        plan__plan_type=membership.plan.plan_type,
        operational_status="ACTIVE"
    ).exclude(id=membership.id).exists()

    if existing_active:
        raise MembershipError("Ya existe una membresía activa para este cliente.")

    # Recalcular fechas
    membership.start_date = today
    membership.end_date = today + timedelta(days=membership.plan.duration_days - 1)
    membership.operational_status = "ACTIVE"

    membership.save(update_fields=[
        "start_date",
        "end_date",
        "renovation_date",
        "operational_status"
    ])

    # Reordenar futuras SCHEDULED
    next_start = membership.end_date + timedelta(days=1)

    future_queue = (
        Membership.objects
        .filter(
            client=membership.client,
            gym=membership.gym,
            plan__plan_type=membership.plan.plan_type,
            operational_status="SCHEDULED",
            start_date__gt=membership.start_date
        )
        .order_by("start_date")
    )

    for future in future_queue:
        future.start_date = next_start
        future.end_date = next_start + timedelta(days=future.plan.duration_days - 1)
        future.save(update_fields=["start_date", "end_date", "renovation_date"])
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
    
    has_future_queue = Membership.objects.filter(
        client=membership.client,
        gym=membership.gym,
        plan__plan_type=membership.plan.plan_type,
        operational_status="SCHEDULED"
    ).exists()

    if has_future_queue:
        raise MembershipError(
            "No se puede congelar una membresía que ya tiene renovaciones programadas en cola."
        )

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

    if membership.client.hikvision_id:
        revoke_hikvision_access(membership)

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

    future_queue = Membership.objects.filter(
        client=membership.client,
        gym=membership.gym,
        plan__plan_type=membership.plan.plan_type,
        operational_status="SCHEDULED",
        start_date__gt=membership.start_date
    ).order_by("start_date")

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
        "renovation_date",
        "total_freeze_days",
        "operational_status",
        "freeze_start_date",
        "unfreeze_requested_by",
        "unfreeze_timestamp"
    ])

    next_start = membership.end_date + timedelta(days=1)

    for future in future_queue:
        future.start_date = next_start
        future.end_date = next_start + timedelta(days=future.plan.duration_days - 1)
        future.save(update_fields=["start_date", "end_date", "renovation_date"])
        next_start = future.end_date + timedelta(days=1)    

    
    sync_hikvision_async(membership)

    return membership


@transaction.atomic
def upgrade_membership_service(
    *,
    client,
    gym,
    new_plan_id,
    payment_method_id,
    created_by,
    notes="Upgrade de membresía",
    paid_amount=0,
    sale_type="CASH",
):

    today = timezone.localdate()

    new_plan = Plan.objects.get(id=new_plan_id)

    active_membership = Membership.objects.filter(
        client=client,
        gym=gym,
        operational_status="ACTIVE",
        plan__plan_type=new_plan.plan_type,
    ).select_related("plan").first()

    if not active_membership:
        raise MembershipError("El cliente no tiene una membresía activa para hacer upgrade.")

    if active_membership.balance > 0 or active_membership.financial_status != "PAID":
        raise MembershipError("No se puede hacer upgrade sobre una membresía con saldo pendiente.")

    if new_plan.gym_id != gym.id:
        raise MembershipError("El plan no pertenece a este gimnasio.")

    if new_plan.plan_type != active_membership.plan.plan_type:
        raise MembershipError("El upgrade solo es permitido entre planes del mismo tipo.")

    if active_membership.plan_id == new_plan.id:
        raise MembershipError("El nuevo plan no puede ser el mismo plan actual.")

    if active_membership.plan.plan_type == "TIME":
        remaining_days = (active_membership.end_date - today).days
        if remaining_days < 0:
            remaining_days = 0

        daily_price = active_membership.final_price / active_membership.plan.duration_days
        upgrade_credit = (daily_price * remaining_days).quantize(Decimal("0.01"))

    elif active_membership.plan.plan_type == "SESSIONS":
        total_sessions = active_membership.sessions_total or 0
        remaining_sessions = active_membership.sessions_remaining or 0

        if total_sessions <= 0:
            raise MembershipError("El plan actual no tiene sesiones válidas para calcular upgrade.")

        session_price = active_membership.final_price / total_sessions
        upgrade_credit = (session_price * remaining_sessions).quantize(Decimal("0.01"))

    else:
        raise MembershipError("Tipo de plan no soportado para upgrade.")

    active_membership.operational_status = "CANCELLED"
    active_membership.end_date = today
    active_membership.save(update_fields=["operational_status", "end_date"])

    new_membership = create_membership_service(
        client=client,
        gym=gym,
        plan_id=new_plan.id,
        requested_start_date=today,
        created_by=created_by,
        notes=notes,
        sale_type=sale_type,
        paid_amount=paid_amount,
        payment_method_id=payment_method_id,
        force_operational_status="ACTIVE",
    )

    new_membership.upgrade_credit = upgrade_credit
    new_membership.action = "UPGRADE"
    new_membership.save()

    return new_membership