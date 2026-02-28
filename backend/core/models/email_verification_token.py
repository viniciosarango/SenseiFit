import uuid
from django.db import models
from django.utils import timezone


class EmailVerificationToken(models.Model):
    token = models.UUIDField(default=uuid.uuid4, unique=True, db_index=True, editable=False)

    contact_point = models.ForeignKey(
        "core.ContactPoint",
        on_delete=models.CASCADE,
        related_name="email_verification_tokens",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at"]),
        ]

    @property
    def is_used(self):
        return self.used_at is not None

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    def __str__(self):
        return f"{self.contact_point_id} {self.token}"