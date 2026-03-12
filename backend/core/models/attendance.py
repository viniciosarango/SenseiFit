from django.db import models
from django.core.exceptions import ValidationError


class Attendance(models.Model):

    METHODS = [
        ('FINGERPRINT', 'Huella Digital'),
        ('QR', 'Código QR'),
        ('MANUAL', 'Manual/Secretaria'),
        ('FACE', 'Reconocimiento Facial'),
        ('CARD', 'Tarjeta RFID'),
    ]

    ACCESS_STATUS = [
        ('GRANTED', 'Acceso Permitido'),
        ('DENIED', 'Acceso Denegado'),
    ]

    client = models.ForeignKey(
        'core.Client',
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    gym = models.ForeignKey(
        'core.Gym',
        on_delete=models.CASCADE,
        related_name='attendances'
    )

    membership = models.ForeignKey(
        'core.Membership',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    check_in_time = models.DateTimeField(auto_now_add=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    is_allowed = models.BooleanField(default=True)

    method = models.CharField(
        max_length=20,
        choices=METHODS,
        default='FINGERPRINT'
    )

    access_status = models.CharField(
        max_length=10,
        choices=ACCESS_STATUS,
        default='GRANTED'
    )

    message_displayed = models.CharField(
        max_length=255,
        blank=True
    )

    device_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID del dispositivo (lector, tablet, torniquete, etc.)"
    )

    source_ip = models.GenericIPAddressField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-check_in_time']

        indexes = [
            models.Index(fields=['gym']),
            models.Index(fields=['client']),
            models.Index(fields=['check_in_time']),
            models.Index(fields=['gym', 'check_in_time']),
        ]

    def clean(self):
        if self.client and self.gym:
            if not self.client.gym_links.filter(gym_id=self.gym_id).exists():
                raise ValidationError(
                    "El cliente no pertenece a este gimnasio."
                )

    def __str__(self):
        return f"{self.client.full_name} - {self.gym.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"




class HikvisionAccessEvent(models.Model):
    """
    Evento crudo recibido desde Hikvision o desde el gateway local.
    Este modelo NO reemplaza Attendance todavía.
    Es una capa paralela, segura y auditable.
    """

    DIRECTION_CHOICES = [
        ("ENTRY", "Entrada"),
        ("EXIT", "Salida"),
        ("UNKNOWN", "Desconocida"),
    ]

    PROCESSING_STATUS_CHOICES = [
        ("PENDING", "Pendiente"),
        ("PROCESSED", "Procesado"),
        ("IGNORED", "Ignorado"),
        ("FAILED", "Fallido"),
    ]

    gym = models.ForeignKey(
        'core.Gym',
        on_delete=models.CASCADE,
        related_name='hikvision_access_events',
        null=True,
        blank=True,
    )

    client = models.ForeignKey(
        'core.Client',
        on_delete=models.SET_NULL,
        related_name='hikvision_access_events',
        null=True,
        blank=True,
    )

    membership = models.ForeignKey(
        'core.Membership',
        on_delete=models.SET_NULL,
        related_name='hikvision_access_events',
        null=True,
        blank=True,
    )

    external_event_id = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID único del evento en Hikvision o en el gateway, si existe."
    )

    event_fingerprint = models.CharField(
        max_length=255,
        unique=True,
        help_text="Hash o fingerprint único para evitar duplicados."
    )

    hikvision_person_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="Person ID / employeeNo / identificador recibido desde Hikvision."
    )

    device_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_index=True,
        help_text="ID o serial del dispositivo que originó el evento."
    )

    device_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Nombre descriptivo del dispositivo."
    )

    direction = models.CharField(
        max_length=10,
        choices=DIRECTION_CHOICES,
        default="UNKNOWN",
        db_index=True,
    )

    method = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Método detectado: FACE, FINGERPRINT, CARD, QR, etc."
    )

    ACCESS_RESULT_CHOICES = [
        ("granted", "Acceso permitido"),
        ("denied", "Acceso denegado"),
        ("unknown_person", "Persona no reconocida"),
        ("", "Sin resultado"),
    ]

    access_result = models.CharField(
        max_length=20,
        choices=ACCESS_RESULT_CHOICES,
        blank=True,
        default="",
        help_text="Resultado técnico del evento."
    )

    occurred_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Momento real en que ocurrió el evento en el dispositivo."
    )

    received_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="Momento en que el backend recibió el evento."
    )

    source_ip = models.GenericIPAddressField(
        null=True,
        blank=True
    )

    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default="PENDING",
        db_index=True,
    )

    processing_error = models.TextField(
        blank=True,
        default=""
    )

    raw_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Payload original recibido desde Hikvision o gateway."
    )

    notes = models.TextField(
        blank=True,
        default=""
    )

    class Meta:
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["gym", "received_at"]),
            models.Index(fields=["client", "received_at"]),
            models.Index(fields=["hikvision_person_id"]),
            models.Index(fields=["device_id", "received_at"]),
            models.Index(fields=["direction", "received_at"]),
            models.Index(fields=["processing_status", "received_at"]),
        ]

    def __str__(self):
        return f"{self.hikvision_person_id or 'UNKNOWN'} - {self.direction} - {self.received_at:%Y-%m-%d %H:%M:%S}"