from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal


class Membership(models.Model):

    OPERATIONAL_STATUS = [
        ('ACTIVE', 'Activa'),
        ('SCHEDULED', 'Programada'),
        ('EXPIRED', 'Vencida'),
        ('CANCELLED', 'Cancelada'),
        ('INACTIVE', 'Inactiva'),
        ('FROZEN', 'Congelada'),
    ]

    ACTION_CHOICES = [
        ("INSCRIPTION", "Inscripción"),
        ("RENEWAL", "Renovación"),
        ("UPGRADE", "Upgrade"),
    ]

    FINANCIAL_STATUS_CHOICES = [
        ('Deuda', 'Deuda'),
        ('Parcial', 'Parcial'),
        ('Pagado', 'Pagado'),
    ]

    SALE_TYPE_CHOICES = [
        ("CASH", "Contado"),
        ("CREDIT", "Crédito"),
    ]

    sale_type = models.CharField(
        max_length=10,
        choices=SALE_TYPE_CHOICES,
        default="CASH"
    )

    payment_grace_days_override = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Override de días de gracia para esta membresía. Si es null, usa el valor del gym."
    )

    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default="INSCRIPTION",
        verbose_name="Tipo de operación"
    )


    upgrade_credit = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    client = models.ForeignKey(
        "core.Client",
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    gym = models.ForeignKey(
        "core.Gym",
        on_delete=models.CASCADE,
        related_name='memberships'
    )

    plan = models.ForeignKey(
        "core.Plan",
        on_delete=models.PROTECT
    )

    # ----------------------
    # TIEMPOS
    # ----------------------
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    payment_due_date = models.DateField(null=True, blank=True)

    
    # ----------------------
    # PRECIOS
    # ----------------------
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    enrollment_fee_applied = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # ----------------------
    # ESTADO FINANCIERO
    # ----------------------
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    financial_status = models.CharField(
        max_length=20,
        choices=FINANCIAL_STATUS_CHOICES,
        default='Deuda'
    )

    # ----------------------
    # ESTADO OPERATIVO
    # ----------------------
    operational_status = models.CharField(
        max_length=20,
        choices=OPERATIONAL_STATUS,
        default='SCHEDULED'
    )

    # ----------------------
    # CONTROL
    # ----------------------
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    notes = models.TextField(blank=True, null=True)

    is_synced_with_hik = models.BooleanField(
        default=False,
        help_text="Indica si la fecha de vencimiento se envió correctamente a la lectora."
    )

    sessions_total = models.IntegerField(default=0)
    sessions_consumed = models.IntegerField(default=0)

    courtesy_qty = models.PositiveIntegerField(default=0)
    courtesy_used = models.PositiveIntegerField(default=0)

    # ----------------------
    # FREEZE CONTROL
    # ----------------------
    freeze_start_date = models.DateField(null=True, blank=True)
    total_freeze_days = models.PositiveIntegerField(default=0)

    freeze_requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="freezes_done"
    )

    unfreeze_requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="unfreezes_done"
    )

    freeze_timestamp = models.DateTimeField(null=True, blank=True)
    unfreeze_timestamp = models.DateTimeField(null=True, blank=True)

    # ============================================================
    # VALIDACIONES PROFESIONALES
    # ============================================================

    def clean(self):
        super().clean()

        # 1️⃣ Cliente debe estar vinculado al gym (ClientGym)
        if self.client_id and self.gym_id:
            if not self.client.gym_links.filter(gym_id=self.gym_id).exists():
                raise ValidationError("El cliente no pertenece a este gimnasio.")

        # 2️⃣ Plan debe pertenecer al mismo gym
        if self.plan and self.gym and self.plan.gym_id != self.gym_id:
            raise ValidationError("El plan no pertenece a este gimnasio.")

        # 3️⃣ ACTIVE requiere fechas
        if self.operational_status == "ACTIVE":
            if not self.start_date or not self.end_date:
                raise ValidationError(
                    "Una membresía ACTIVA debe tener fecha de inicio y fin."
                )

        # 4️⃣ Fin no puede ser menor a inicio
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError(
                    "La fecha de fin no puede ser menor a la fecha de inicio."
                )

    # ============================================================
    # PROPIEDADES
    # ============================================================

    @property
    def sessions_remaining(self):
        return max(0, self.sessions_total - self.sessions_consumed)

    # ============================================================
    # SAVE BLINDADO
    # ============================================================

    def save(self, *args, **kwargs):

        # Inicializa sesiones si es nueva y es plan por sesiones
        if not self.pk and self.plan.plan_type == 'SESSIONS':
            self.sessions_total = self.plan.total_sessions

        orig = Decimal(str(self.original_price or 0))
        disc_per = Decimal(str(self.discount_percent_applied or 0))
        enrollment = Decimal(str(self.enrollment_fee_applied or 0))
        u_credit = Decimal(str(self.upgrade_credit or 0))

        self.final_price = orig - (orig * (disc_per / 100))
        self.total_amount = self.final_price + enrollment - u_credit
        self.balance = max(Decimal('0.00'), self.total_amount - self.paid_amount)

        if self.balance == 0:
            self.financial_status = 'Pagado'
        elif self.balance < self.total_amount:
            self.financial_status = 'Parcial'
        else:
            self.financial_status = 'Deuda'

        # ✅ AHORA validamos con todos los valores ya calculados
        self.full_clean()

        super().save(*args, **kwargs)

    # ============================================================
    # META
    # ============================================================

    class Meta:
        indexes = [
            models.Index(fields=["gym", "client"]),
            models.Index(fields=["operational_status"]),
            models.Index(fields=["financial_status"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["client", "gym", "plan"],
                condition=models.Q(operational_status="ACTIVE"),
                name="uniq_active_membership_per_client_gym_plan"
            )
        ]

    def __str__(self):
        return f"{self.client} - {self.plan.name} - ({self.financial_status})"
