from django.db import models

class Branch(models.Model):
    gym = models.ForeignKey('Gym', on_delete=models.CASCADE, related_name='branches')
    address = models.OneToOneField('Address', on_delete=models.SET_NULL, null=True, blank=True)
    
    name = models.CharField(max_length=100, verbose_name="Nombre de la Sucursal")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Teléfono de la Sede")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gym.name} - {self.name}"

    class Meta:
        verbose_name = "Sucursal"
        verbose_name_plural = "Sucursales"