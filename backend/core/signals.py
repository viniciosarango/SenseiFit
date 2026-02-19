from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
from .models.payment import Payment

@receiver([post_save, post_delete], sender=Payment)
def update_membership_status(sender, instance, **kwargs):
    if instance.membership:
        membership = instance.membership
        
        # 1. Sumamos pagos
        total_paid = membership.payments.exclude(status='Anulado').aggregate(total=Sum('amount'))['total'] or 0
        
        # 2. Reflejamos la realidad
        membership.paid_amount = total_paid
        membership.balance = membership.total_amount - total_paid
        
        # 3. LÓGICA DE FECHA LÍMITE (Centralizada aquí)
        if membership.balance > 0:
            if not membership.payment_due_date:
                grace_days = membership.gym.default_payment_grace_days
                membership.payment_due_date = timezone.now().date() + timedelta(days=grace_days)
            membership.financial_status = 'Parcial' if total_paid > 0 else 'Deuda'
        else:
            membership.payment_due_date = None
            membership.financial_status = 'Pagado'
            
        # 🎯 PROTECCIÓN: Evitar saldos negativos visuales (opcional)
        # if membership.balance < 0: membership.balance = 0

        membership.save(update_fields=['paid_amount', 'balance', 'financial_status', 'payment_due_date'])