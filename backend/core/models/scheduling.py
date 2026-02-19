from django.db import models
from .gym import Gym
from .client import Client

class Service(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_capacity = models.IntegerField()
    def __str__(self): return self.name

class GymClass(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    schedule = models.CharField(max_length=100)
    max_capacity = models.IntegerField()
    def __str__(self): return self.name

class Reservation(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    gym_class = models.ForeignKey(GymClass, on_delete=models.CASCADE)
    status = models.CharField(max_length=50) # confirmada, cancelada

    