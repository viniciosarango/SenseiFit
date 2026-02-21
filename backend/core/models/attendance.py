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
            if self.client.gym != self.gym:
                raise ValidationError(
                    "El cliente no pertenece a este gimnasio."
                )

    def __str__(self):
        return f"{self.client.full_name} - {self.gym.name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"

