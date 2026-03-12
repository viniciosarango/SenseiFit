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
    # Configuración pantalla TV
    # -------------------------
    tv_idle_mode = models.CharField(
        max_length=20,
        default="text",
        help_text="Modo idle de la TV: text, image, video, youtube"
    )

    tv_idle_title = models.CharField(
        max_length=150,
        blank=True,
        default="Dorians Gym"
    )

    tv_idle_subtitle = models.CharField(
        max_length=150,
        blank=True,
        default="¡Transforma tu vida!"
    )

    tv_idle_message = models.CharField(
        max_length=255,
        blank=True,
        default="Esperando próximo acceso..."
    )

    tv_idle_image_url = models.URLField(
        blank=True,
        default=""
    )

    tv_idle_video_url = models.URLField(
        blank=True,
        default=""
    )

    tv_idle_youtube_url = models.URLField(
        blank=True,
        default=""
    )

    tv_event_display_seconds = models.PositiveIntegerField(
        default=10,
        help_text="Segundos que se muestra el evento antes de volver al modo idle."
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
