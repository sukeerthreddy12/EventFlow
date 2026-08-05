import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class EmailRetryQueue(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        DEAD = "DEAD", "Dead"  # max attempts exceeded

    class Kind(models.TextChoices):
        REGISTRATION_CONFIRMED = "REGISTRATION_CONFIRMED", "Registration confirmed"
        WAITLIST_JOINED = "WAITLIST_JOINED", "Waitlist joined"
        WAITLIST_PROMOTED = "WAITLIST_PROMOTED", "Waitlist promoted"
        EVENT_CANCELLED = "EVENT_CANCELLED", "Event cancelled"
        EVENT_REMINDER = "EVENT_REMINDER", "Event reminder"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=40, choices=Kind.choices)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_retries",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="email_retries",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    attempts = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=5)
    last_error = models.TextField(blank=True)
    next_attempt_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_attempt_at"]
        indexes = [
            models.Index(fields=["status", "next_attempt_at"]),
        ]

    def __str__(self):
        return f"{self.kind} → {self.user_id} ({self.status})"