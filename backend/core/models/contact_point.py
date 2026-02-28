from django.db import models
from django.utils import timezone


class ContactPoint(models.Model):
    class Types(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        PHONE = "PHONE", "Phone"

    company = models.ForeignKey(
        "core.Company",
        on_delete=models.CASCADE,
        related_name="contact_points",
        db_index=True,
    )

    user = models.ForeignKey(
        "core.User",
        on_delete=models.CASCADE,
        related_name="contact_points",
        null=True,
        blank=True,
        help_text="Cuenta asociada (si existe).",
    )

    client = models.ForeignKey(
        "core.Client",
        on_delete=models.CASCADE,
        related_name="contact_points",
        null=True,
        blank=True,
        help_text="Cliente asociado (si existe).",
    )

    type = models.CharField(max_length=10, choices=Types.choices, db_index=True)
    value = models.CharField(max_length=255, db_index=True)

    is_primary = models.BooleanField(default=False, db_index=True)
    is_verified = models.BooleanField(default=False, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["company", "type", "value"]),
            models.Index(fields=["company", "client", "type"]),
            models.Index(fields=["company", "user", "type"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "type", "value"],
                name="uniq_contactpoint_company_type_value",
            ),
        ]

    def mark_verified(self):
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=["is_verified", "verified_at"])

    def __str__(self):
        who = f"client={self.client_id}" if self.client_id else f"user={self.user_id}"
        return f"{self.company_id} {who} {self.type} {self.value}"