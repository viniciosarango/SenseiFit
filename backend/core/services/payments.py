from typing import Optional

from decimal import Decimal
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from core.models import Membership, Payment, PaymentMethod

class PaymentError(Exception):
    pass

@transaction.atomic
def register_payment(
    *,
    membership_id: int,
    amount,
    payment_method_id: int,
    notes: str = "",
    created_by=None,
    set_due_days: Optional[int] = None,
):
    amount = Decimal(str(amount))

    if amount <= 0:
        raise PaymentError("El monto debe ser mayor a 0.")

    try:
        # Bloqueamos la fila para que nadie más la toque mientras cobramos
        membership = (
            Membership.objects.select_for_update()
            .select_related("plan", "client", "gym")
            .get(id=membership_id)
        )
    except Membership.DoesNotExist:
        raise PaymentError("Membresía no encontrada.")

    # 1. Validación de Saldo
    if membership.balance <= 0:
        raise PaymentError("Esta membresía ya está cancelada (Pagado).")

    if amount > membership.balance:
        raise PaymentError(f"El monto excede el saldo pendiente (${membership.balance}).")

    try:
        method = PaymentMethod.objects.get(id=payment_method_id)
    except PaymentMethod.DoesNotExist:
        raise PaymentError("Método de pago inválido o no existe.")

    # 2. CREACIÓN DEL RECIBO (Dispara el Sensor de Honestidad)
    payment = Payment.objects.create(
        membership=membership,
        gym=membership.gym,     # Agregamos gym para reportes directos
        client=membership.client, # Agregamos client para historial rápido
        amount=amount,
        payment_method=method,
        #status="Pagado",        # En español
        notes=notes or "",
        #created_by=created_by,
    )

    # 🔥 Actualizar dinero en la membresía
    membership.paid_amount += amount
    membership.save()

    
    if set_due_days is None:
        # Si no enviaron un valor desde el front, usamos el del Gimnasio
        grace_days = membership.gym.default_payment_grace_days
    else:
        grace_days = set_due_days


    if membership.balance > 0:
        membership.payment_due_date = timezone.now().date() + timedelta(days=grace_days)
    else:
        membership.payment_due_date = None

    membership.save(update_fields=["payment_due_date"])

    return payment, membership



@transaction.atomic
def void_payment(*, payment_id: int, reason: str, user):
    try:
        # Bloqueamos el pago para evitar ediciones simultáneas
        payment = Payment.objects.select_for_update().get(id=payment_id)
    except Payment.DoesNotExist:
        raise PaymentError("El pago no existe en el búnker.")

    if payment.status == 'VOID':
        raise PaymentError("Este pago ya ha sido anulado.")

    membership = payment.membership
    if membership:
        # 🎯 LA CLAVE: Restamos del 'monto pagado'. 
        # El save() del modelo se encargará de subir el 'balance' automáticamente.
        membership.paid_amount -= payment.amount
        
        # Si ahora debe dinero, le ponemos una fecha límite de pago (gracia)
        if (membership.total_amount - membership.paid_amount) > 0:
            grace_days = membership.gym.default_payment_grace_days
            membership.payment_due_date = timezone.now().date() + timedelta(days=grace_days)
        
        membership.save()

    # Marcamos el recibo como anulado y dejamos rastro
    payment.status = 'VOID'
    timestamp = timezone.now().strftime("%Y-%m-%d %H:%M")
    payment.notes = f"{payment.notes or ''}\n--- ANULADO [{timestamp}] POR {user.username}: {reason} ---"
    payment.save()

    return payment