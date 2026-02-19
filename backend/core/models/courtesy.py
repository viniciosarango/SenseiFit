from django.db import models
from .membership import Membership
from .client import Client

class CourtesyPass(models.Model):
    STATUS_CHOICES = [
        ('CREATED', 'Created'), ('SENT', 'Sent'), ('REDEEMED', 'Redeemed'),
        ('EXPIRED', 'Expired'), ('CANCELED', 'Canceled'),
    ]
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE, related_name='courtesy_passes')
    guest_name = models.CharField(max_length=100)
    guest_lastname = models.CharField(max_length=100, blank=True)
    guest_phone = models.CharField(max_length=20)
    guest_id_number = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='CREATED')
    issued_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    converted_client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    
    def __str__(self): return f"Cortesía {self.guest_name}"