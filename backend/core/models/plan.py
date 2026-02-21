from django.db import models
from .gym import Gym
import uuid
from django.core.exceptions import ValidationError


class Plan(models.Model):

    PLAN_TYPES = [
        ('TIME', 'Por Tiempo'),
        ('SESSIONS', 'Por Sesiones'),
    ]

    gym = models.ForeignKey(
        Gym,
        on_delete=models.CASCADE,
        related_name='plans'
    )

    name = models.CharField(max_length=100)

    code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Código interno único por gimnasio."
    )

    description = models.TextField(blank=True)

    plan_type = models.CharField(
        max_length=20,
        choices=PLAN_TYPES,
        default='TIME'
    )

    price = models.DecimalField(max_digits=10, decimal_places=2)

    duration_days = models.IntegerField(default=30)
    total_sessions = models.IntegerField(default=0)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    # ============================================================
    # VALIDACIÓN PROFESIONAL
    # ============================================================

    def clean(self):
        if self.plan_type == "SESSIONS" and self.total_sessions <= 0:
            raise ValidationError("Los planes por sesiones deben tener total_sessions > 0.")

        if self.plan_type == "TIME" and self.duration_days <= 0:
            raise ValidationError("Los planes por tiempo deben tener duración válida.")

    # ============================================================
    # SAVE
    # ============================================================

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = f"PLN-{self.name[:5].upper()}-{uuid.uuid4().hex[:4].upper()}"
        super().save(*args, **kwargs)

    # ============================================================
    # REPRESENTACIÓN
    # ============================================================

    def __str__(self):
        return f"{self.name} - {self.gym.name}"

    # ============================================================
    # META
    # ============================================================

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["gym", "code"],
                name="unique_plan_code_per_gym"
            )
        ]

        indexes = [
            models.Index(fields=["gym"]),
            models.Index(fields=["is_active"]),
        ]
