from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Payment(models.Model):

    STATUS_CHOICES = [
        ('PAID', 'Pagado'),
        ('VOID', 'Anulado'),
    ]

    gym = models.ForeignKey(
        "core.Gym",
        on_delete=models.CASCADE,
        related_name='payments'
    )

    client = models.ForeignKey(
        "core.Client",
        on_delete=models.CASCADE,
        related_name='payments'
    )

    membership = models.ForeignKey(
        "core.Membership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )

    payment_method = models.ForeignKey(
        "core.PaymentMethod",
        on_delete=models.PROTECT
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    payment_date = models.DateTimeField(auto_now_add=True)

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    notes = models.TextField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PAID'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # ============================================================
    # VALIDACIONES PROFESIONALES
    # ============================================================

    def clean(self):
        super().clean()

        # 1️⃣ Monto debe ser positivo
        if self.amount <= 0:
            raise ValidationError("El monto del pago debe ser mayor que cero.")

        # 2️⃣ Cliente debe pertenecer al gym
        if self.client and self.gym and self.client.gym_id != self.gym_id:
            raise ValidationError("El cliente no pertenece a este gimnasio.")

        # 3️⃣ Membership coherente
        if self.membership:
            if self.membership.gym_id != self.gym_id:
                raise ValidationError("La membresía no pertenece a este gimnasio.")

            if self.membership.client_id != self.client_id:
                raise ValidationError("La membresía no pertenece a este cliente.")

        # 4️⃣ PaymentMethod coherente
        if self.payment_method and self.gym:
            if self.payment_method.gym_id != self.gym_id:
                raise ValidationError("El método de pago no pertenece a este gimnasio.")

    # ============================================================
    # SAVE BLINDADO
    # ============================================================

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ============================================================
    # META
    # ============================================================

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

        indexes = [
            models.Index(fields=["gym"]),
            models.Index(fields=["membership"]),
            models.Index(fields=["payment_date"]),
        ]

    def __str__(self):
        return f"Pago {self.id} - {self.client} (${self.amount})"
