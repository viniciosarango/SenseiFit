from django.db import models
from .product import Product

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='stock')
    quantity = models.IntegerField(default=0)
    min_stock = models.IntegerField(default=5)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Stock: {self.product.name} ({self.quantity})"