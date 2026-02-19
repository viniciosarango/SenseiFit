from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Usuario")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Acción")
    model_name = models.CharField(max_length=100, verbose_name="Tabla/Modelo")
    record_id = models.PositiveIntegerField(verbose_name="ID del Registro")
    
    # 📝 Guardamos los cambios en formato JSON (ej: {"precio": [30, 50]})
    details = models.JSONField(blank=True, null=True, verbose_name="Detalles del Cambio")
    
    ip_address = models.GenericIPAddressField(blank=True, null=True, verbose_name="Dirección IP")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y Hora")

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"

    def __str__(self):
        return f"{self.action} en {self.model_name} (ID: {self.record_id})"