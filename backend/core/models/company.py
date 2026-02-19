from django.db import models

class Company(models.Model):
    """El 'Tenant' o Dueño del Negocio que te compra el software"""
    name = models.CharField(max_length=255)
    tax_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Companies"