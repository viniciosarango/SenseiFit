from django.db import models

class ClientGym(models.Model):
    client = models.ForeignKey(
        "core.Client",
        on_delete=models.CASCADE,
        related_name="gym_links"
    )

    gym = models.ForeignKey(
        "core.Gym",
        on_delete=models.CASCADE,
        related_name="client_links"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("client", "gym")

    def __str__(self):
        return f"{self.client.full_name} → {self.gym.name}"