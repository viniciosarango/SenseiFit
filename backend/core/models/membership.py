from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta

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
        ('PENDING', 'Pendiente'),
        ('PARTIAL', 'Parcial'),
        ('PAID', 'Pagado'),
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
    renovation_date = models.DateField(null=True, blank=True, db_index=True)
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
        default='PENDING'
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

        # 3️⃣ Reglas de venta
        if self.sale_type == "CASH" and self.payment_due_date:
            raise ValidationError(
                "Una membresía CASH no puede tener fecha límite de pago."
            )

        if (
            self.sale_type == "CREDIT"
            and self.balance > 0
            and self.operational_status not in ["CANCELLED", "INACTIVE"]
            and not self.payment_due_date
        ):
            raise ValidationError(
                "Una membresía CREDIT con saldo pendiente debe tener fecha límite de pago."
            )        

        # 4 ACTIVE requiere fechas
        if self.operational_status == "ACTIVE":
            if not self.start_date or not self.end_date:
                raise ValidationError(
                    "Una membresía ACTIVA debe tener fecha de inicio y fin."
                )

        # 5 Fin no puede ser menor a inicio
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

        MONEY_Q = Decimal("0.01")

        def q(v):
            return Decimal(str(v or 0)).quantize(MONEY_Q, rounding=ROUND_HALF_UP)

        # Inicializa sesiones si es nueva y es plan por sesiones
        if not self.pk and self.plan.plan_type == 'SESSIONS':
            self.sessions_total = self.plan.total_sessions

        orig = q(self.original_price)
        disc_per = Decimal(str(self.discount_percent_applied or 0))  # % no necesita q
        enrollment = q(self.enrollment_fee_applied)
        u_credit = q(self.upgrade_credit)
        paid = q(self.paid_amount)

        discount_amount = (orig * disc_per / Decimal("100")).quantize(MONEY_Q, rounding=ROUND_HALF_UP)

        self.final_price = (orig - discount_amount).quantize(MONEY_Q, rounding=ROUND_HALF_UP)
        self.total_amount = (self.final_price + enrollment - u_credit).quantize(MONEY_Q, rounding=ROUND_HALF_UP)

        raw_balance = (self.total_amount - paid)
        self.balance = (raw_balance if raw_balance > 0 else Decimal("0.00")).quantize(MONEY_Q, rounding=ROUND_HALF_UP)

        if self.balance == 0:
            self.financial_status = 'PAID'
        elif self.balance < self.total_amount:
            self.financial_status = 'PARTIAL'
        else:
            self.financial_status = 'PENDING'

        # ✅ AHORA validamos con todos los valores ya calculados
        if self.end_date:
            self.renovation_date = self.end_date + timedelta(days=1)
        else:
            self.renovation_date = None
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
