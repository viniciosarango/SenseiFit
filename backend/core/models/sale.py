from django.db import models
from .gym import Gym
from .client import Client
from .product import Product

class Sale(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta: {self.product.name} a {self.client.first_name}"