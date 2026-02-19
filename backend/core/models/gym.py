from django.db import models
from .company import Company


class Gym(models.Model):
    """
    Sucursal física perteneciente a una Company (multi-tenant).
    """

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='gyms'
    )

    name = models.CharField(max_length=100)

    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    # -------------------------
    # Identidad visual (branding)
    # -------------------------
    logo = models.ImageField(upload_to="gym_logos/", blank=True, null=True)
    primary_color = models.CharField(max_length=20, blank=True, null=True)
    secondary_color = models.CharField(max_length=20, blank=True, null=True)

    # -------------------------
    # Configuración financiera
    # -------------------------
    currency = models.CharField(max_length=10, default="USD")
    default_payment_grace_days = models.PositiveIntegerField(
        default=7,
        verbose_name="Días de gracia para pagos parciales"
    )

    # -------------------------
    # Configuración de acceso
    # -------------------------
    access_control_enabled = models.BooleanField(default=True)
    auto_block_on_debt = models.BooleanField(default=True)

    # -------------------------
    # Mensajes automáticos
    # -------------------------
    birthday_message = models.CharField(
        max_length=255,
        default="¡Feliz cumpleaños {name}! 🎉 Pasa por el bar por tu regalo."
    )

    expiration_alert_message = models.CharField(
        max_length=255,
        default="¡Hola {name}! Te quedan {days} días activos. ¡No olvides renovar!"
    )

    # -------------------------
    # Estado del gym
    # -------------------------
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.company.name})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "name"],
                name="unique_gym_name_per_company"
            )
        ]

        indexes = [
            models.Index(fields=["company"]),
            models.Index(fields=["is_active"]),
        ]
