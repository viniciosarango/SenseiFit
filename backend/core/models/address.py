from django.db import models

class Address(models.Model):
    street_main = models.CharField(max_length=255, verbose_name="Calle Principal")
    street_secondary = models.CharField(max_length=255, blank=True, null=True, verbose_name="Calle Secundaria")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    state = models.CharField(max_length=100, verbose_name="Estado/Provincia")
    zip_code = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Postal")
    country = models.CharField(max_length=100, default="Ecuador", verbose_name="País")
    
    # 🛰️ Coordenadas para el mapa del Frontend
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.street_main}, {self.city}"

    class Meta:
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"