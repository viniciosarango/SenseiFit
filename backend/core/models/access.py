from django.db import models
from django.utils import timezone

class AccessToken(models.Model):
    TOKEN_TYPES = [
        ('QR', 'Código QR'),
        ('BARCODE', 'Código de Barras'),
        ('RFID', 'Tarjeta RFID'),
        ('BIOMETRIC', 'Huella/Rostro'),
    ]

    client = models.ForeignKey('Client', on_delete=models.CASCADE, related_name='access_tokens')
    membership = models.ForeignKey('Membership', on_delete=models.SET_NULL, null=True, blank=True)
    
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPES, default='QR')
    token_value = models.CharField(max_length=255, unique=True, verbose_name="Valor del Token")
    
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    
    max_uses = models.PositiveIntegerField(default=0, help_text="0 para usos ilimitados")
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token {self.token_type} - {self.client.full_name}"



class AccessLog(models.Model):
    RESULTS = [
        ('SUCCESS', 'Acceso Permitido'),
        ('DENIED', 'Acceso Denegado'),
    ]

    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, verbose_name="Sucursal")
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True)
    token_value = models.CharField(max_length=255)
    
    access_result = models.CharField(max_length=10, choices=RESULTS)
    denial_reason = models.CharField(max_length=255, blank=True, null=True)
    
    attempt_time = models.DateTimeField(auto_now_add=True)
    device_ip = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        verbose_name = "Registro de Acceso"
        verbose_name_plural = "Registros de Acceso"
        ordering = ['-attempt_time']


