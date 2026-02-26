from typing import Optional

from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from core.models import Membership, Payment, PaymentMethod
from django.db.models import Sum

class PaymentError(Exception):
    pass

@transaction.atomic
def register_payment(*, membership_id, amount, payment_method_id, notes="", created_by=None):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise PaymentError("El monto debe ser mayor a 0.")

    # 🔒 Bloquear membresía
    try:
        membership = Membership.objects.select_for_update().get(id=membership_id)
    except Membership.DoesNotExist:
        raise PaymentError("Membresía no encontrada.")

    # ✅ Balance actual (de DB)
    balance_before = Decimal(str(membership.balance or 0))

    if balance_before <= 0:
        raise PaymentError("Esta membresía ya está cancelada (Pagado).")

    if amount > balance_before:
        raise PaymentError(f"El monto excede el saldo pendiente (${balance_before}).")

    # ✅ Validar método de pago (ideal: validar que sea del mismo gym)
    try:
        pm = PaymentMethod.objects.get(id=payment_method_id)
    except PaymentMethod.DoesNotExist:
        raise PaymentError("Método de pago inválido o no existe.")

    if pm.gym_id != membership.gym_id:
        raise PaymentError("El método de pago no pertenece a este gimnasio.")

    # 1) Crear pago (snapshot BEFORE)
    payment = Payment.objects.create(
        membership=membership,
        gym=membership.gym,
        client=membership.client,
        amount=amount,
        payment_method_id=payment_method_id,
        notes=notes,
        created_by=created_by,
        balance_before=balance_before,
        balance_after=balance_before,  # temporal
        status="PAID",
    )

    # 2) Recalcular finanzas SIEMPRE desde la DB (solo PAID)
    membership = recalc_membership_finance(membership)

    # 3) Anti-exceso (después del recálculo, por si hubo race condition)
    if membership.paid_amount > Decimal(str(membership.total_amount)):
        raise PaymentError(
            f"El pago total (${membership.paid_amount}) excede el precio del plan (${membership.total_amount})."
        )

    # 4) Snapshot AFTER real
    payment.balance_after = Decimal(str(membership.balance or 0))
    payment.save(update_fields=["balance_after"])

    return payment, membership





def recalc_membership_finance(membership: Membership) -> Membership:
    """
    Fuente de verdad:
    - paid_amount = SUM(Payment.amount WHERE status='PAID' AND membership=membership)
    - balance/financial_status se recalculan en Membership.save()
    """
    total_pagado = (
        Payment.objects.filter(membership_id=membership.id, status="PAID")
        .aggregate(s=Sum("amount"))["s"]
        or Decimal("0.00")
    )

    membership.paid_amount = total_pagado

    # payment_due_date depende de si queda saldo (usa total_pagado, NO membership.balance viejo)
    provisional_balance = max(Decimal("0.00"), Decimal(str(membership.total_amount)) - total_pagado)
    if provisional_balance > 0:
        grace_days = membership.gym.default_payment_grace_days
        membership.payment_due_date = timezone.localdate() + timedelta(days=grace_days)
    else:
        membership.payment_due_date = None

    membership.save()  # recalcula balance + financial_status internamente
    return membership





@transaction.atomic
def void_payment(*, payment_id: int, reason: str, user):
    # 🔒 bloquear pago
    try:
        payment = Payment.objects.select_for_update().get(id=payment_id)
    except Payment.DoesNotExist:
        raise PaymentError("El pago no existe.")

    if payment.status == "VOID":
        raise PaymentError("Este pago ya ha sido anulado.")

    membership = None
    if payment.membership_id:
        # 🔒 bloquear membresía (sin outer join)
        membership = Membership.objects.select_for_update().get(id=payment.membership_id)

    # 1) marcar VOID + auditoría
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
    payment.status = "VOID"
    payment.notes = f"{payment.notes or ''}\n--- ANULADO [{timestamp}] POR {user.username}: {reason} ---"
    payment.save(update_fields=["status", "notes"])

    # 2) recalcular finanzas desde DB (solo PAID)
    if membership:
        recalc_membership_finance(membership)

    return payment