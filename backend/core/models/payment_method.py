from django.db import models


class PaymentMethod(models.Model):

    gym = models.ForeignKey(
        'core.Gym',
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )

    name = models.CharField(
        max_length=100,
        help_text="Ej: Efectivo, Transferencia, Tarjeta"
    )

    active = models.BooleanField(default=True)

    description = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # ============================================================
    # REPRESENTACIÓN
    # ============================================================

    def __str__(self):
        scope = self.gym.name if self.gym else "Global"
        return f"{self.name} ({scope})"

    # ============================================================
    # META
    # ============================================================

    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"

        constraints = [
            models.UniqueConstraint(
                fields=["gym", "name"],
                name="unique_payment_method_per_gym"
            )
        ]

        indexes = [
            models.Index(fields=["gym"]),
            models.Index(fields=["active"]),
        ]
