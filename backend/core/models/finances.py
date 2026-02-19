from django.db import models
from django.conf import settings

class Income(models.Model):
    INCOME_CATEGORIES = [
        ('MEMBERSHIP', 'Membresía'),
        ('SALE', 'Venta Productos'),
        ('EVENT', 'Evento'),
        ('RENTAL', 'Alquiler Espacio'),
        ('OTHER', 'Otros'),
    ]

    gym = models.ForeignKey('Gym', on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, verbose_name="Sucursal")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    description = models.CharField(max_length=255, verbose_name="Descripción")
    category = models.CharField(max_length=50, choices=INCOME_CATEGORIES, default='OTHER')
    date = models.DateField(verbose_name="Fecha de Ingreso")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ingreso: {self.amount} - {self.description}"




class Expense(models.Model):
    EXPENSE_CATEGORIES = [
        ('UTILITIES', 'Servicios Básicos'),
        ('RENT', 'Arriendo'),
        ('SALARY', 'Nómina/Sueldos'),
        ('MAINTENANCE', 'Mantenimiento'),
        ('SUPPLIES', 'Suministros'),
        ('OTHER', 'Otros'),
    ]

    gym = models.ForeignKey('Gym', on_delete=models.CASCADE)
    branch = models.ForeignKey('Branch', on_delete=models.CASCADE, verbose_name="Sucursal")
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Monto")
    description = models.CharField(max_length=255, verbose_name="Descripción")
    category = models.CharField(max_length=50, choices=EXPENSE_CATEGORIES, default='OTHER')
    date = models.DateField(verbose_name="Fecha de Gasto")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, verbose_name="Aprobado por")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gasto: {self.amount} - {self.description}"