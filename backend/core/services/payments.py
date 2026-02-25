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

    # 🔒 bloqueamos la membresía
    try:
        membership = Membership.objects.select_for_update().get(id=membership_id)
    except Membership.DoesNotExist:
        raise PaymentError("Membresía no encontrada.")

    balance_before = Decimal(str(membership.balance or 0))

    if balance_before <= 0:
        raise PaymentError("Esta membresía ya está cancelada (Pagado).")

    if amount > balance_before:
        raise PaymentError(f"El monto excede el saldo pendiente (${balance_before}).")

    try:
        PaymentMethod.objects.get(id=payment_method_id)
    except PaymentMethod.DoesNotExist:
        raise PaymentError("Método de pago inválido o no existe.")

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
        balance_after=balance_before,  # temporal, se actualiza luego
    )

    # 2) total real desde DB (solo PAID)
    total_pagado = Payment.objects.filter(
        membership=membership,
        status="PAID"
    ).aggregate(Sum("amount"))["amount__sum"] or Decimal("0.00")

    if total_pagado > Decimal(str(membership.total_amount)):
        raise PaymentError(
            f"El pago total (${total_pagado}) excede el precio del plan (${membership.total_amount})."
        )

    # 3) actualizar membresía
    membership.paid_amount = total_pagado

    provisional_balance = max(Decimal("0.00"), Decimal(str(membership.total_amount)) - total_pagado)

    if provisional_balance > 0:
        grace_days = membership.gym.default_payment_grace_days
        membership.payment_due_date = timezone.localdate() + timedelta(days=grace_days)
    else:
        membership.payment_due_date = None

    membership.save()

    # 4) snapshot AFTER real
    payment.balance_after = Decimal(str(membership.balance or 0))
    payment.save(update_fields=["balance_after"])

    return payment, membership



@transaction.atomic
def void_payment(*, payment_id: int, reason: str, user):
    try:
        payment = Payment.objects.select_for_update().get(id=payment_id)
    except Payment.DoesNotExist:
        raise PaymentError("El pago no existe.")

    if payment.status == "VOID":
        raise PaymentError("Este pago ya ha sido anulado.")

    membership = None
    if payment.membership_id:
        membership = Membership.objects.select_for_update().get(id=payment.membership_id)

    # 1) Marcar el pago como anulado + auditoría
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
    payment.status = "VOID"
    payment.notes = f"{payment.notes or ''}\n--- ANULADO [{timestamp}] POR {user.username}: {reason} ---"
    payment.save(update_fields=["status", "notes"])

    # 2) Recalcular el total pagado REAL desde DB (solo pagos PAID)
    if membership:
        total_pagado = Payment.objects.filter(
            membership_id=membership.id,
            status="PAID"
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

        membership.paid_amount = total_pagado

        # calcular saldo real (sin depender del campo balance antes del save)
        provisional_balance = max(Decimal("0.00"), membership.total_amount - total_pagado)

        grace_days = membership.gym.default_payment_grace_days
        membership.payment_due_date = (
            timezone.localdate() + timedelta(days=grace_days)
            if provisional_balance > 0
            else None
        )

        membership.save()

    return payment