from django.db import models


class NotificationTemplate(models.Model):

    TYPE_CHOICES = [
        ('WELCOME', 'Bienvenida'),
        ('PAYMENT_REMINDER', 'Recordatorio de Pago'),
        ('MEMBERSHIP_EXPIRED', 'Membresía Vencida'),
        ('PROMOTION', 'Promoción'),
        ('ALERT', 'Alerta'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)

    subject = models.CharField(max_length=255, blank=True, null=True)
    body = models.TextField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["type"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.name}"


class Notification(models.Model):

    CHANNEL_CHOICES = [
        ('WHATSAPP', 'WhatsApp'),
        ('EMAIL', 'Email'),
        ('SMS', 'SMS'),
        ('APP', 'Push App'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('SENT', 'Enviado'),
        ('FAILED', 'Fallido'),
        ('RETRY', 'Reintento'),
    ]

    gym = models.ForeignKey(
        'Gym',
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    client = models.ForeignKey(
        'Client',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications'
    )

    template = models.ForeignKey(
        'NotificationTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    channel = models.CharField(max_length=15, choices=CHANNEL_CHOICES)

    destination = models.CharField(max_length=255)
    message_sent = models.TextField()

    provider = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Proveedor usado (Twilio, SMTP, Meta API, etc.)"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )

    error_message = models.TextField(blank=True, null=True)

    attempts = models.PositiveIntegerField(default=0)

    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gym']),
            models.Index(fields=['status']),
            models.Index(fields=['channel']),
        ]

    def __str__(self):
        return f"{self.channel} - {self.destination} - {self.status}"
