import uuid

from django.conf import settings
from django.db import models


class Registration(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        WAITLISTED = "WAITLISTED", "Waitlisted"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            # One ACTIVE registration per user per event (allows re-register after CANCELLED)
            models.UniqueConstraint(
                fields=["user", "event"],
                condition=models.Q(status__in=["CONFIRMED", "WAITLISTED"]),
                name="unique_active_registration_per_user_event",
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.event_id} ({self.status})"

# Create your models here.
