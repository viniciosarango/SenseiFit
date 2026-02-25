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
    membership = Membership.objects.get(id=membership_id)
    amount = Decimal(str(amount))

    # 1. CREAR EL PAGO PRIMERO (Para que exista en la DB)
    payment = Payment.objects.create(
        membership=membership,
        gym=membership.gym,
        client=membership.client,
        amount=amount,
        payment_method_id=payment_method_id,
        notes=notes,
        created_by=created_by
    )

    # 2. CALCULAR EL TOTAL REAL DESDE LA DB
    total_pagado = Payment.objects.filter(
        membership=membership,
        status='PAID'
    ).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

    # 3. VALIDACIÓN ANTI-EXCESO (Después de sumar)
    # Si la suma de pagos supera el precio del plan, hay un error
    if total_pagado > membership.total_amount:
        # Opcional: podrías revertir el pago aquí si quieres ser estricto
        raise PaymentError(f"El pago total (${total_pagado}) excede el precio del plan (${membership.total_amount}).")

    # 4. ACTUALIZAR MEMBRESÍA
    membership.paid_amount = total_pagado
    
    # Lógica de fechas de gracia
    if membership.balance > 0:
        membership.payment_due_date = timezone.localdate() + timedelta(days=7)
    else:
        membership.payment_due_date = None
        
    membership.save() # Esto recalcula el balance automáticamente

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