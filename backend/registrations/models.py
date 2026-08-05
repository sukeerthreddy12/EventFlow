import uuid

from django.conf import settings
from django.db import models
import secrets 


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
    team = models.ForeignKey(
    "registrations.TeamRegistration",
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name="registrations",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reminder_sent_at = models.DateTimeField(null=True, blank=True)

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


class TeamRegistration(models.Model) : 
    """
    Group signup led by one user.
    Waitlist rule (all-or-nothing, FIFO, no skip):
    - On register: whole team is CONFIRMED or whole team is WAITLISTED.
    - On promote: oldest waitlisted party first; promote only if free seats
      >= party size; if not enough seats, stop (do not skip to a smaller party).
    """


    class Status(models.TextChoices):
        CONFIRMED = "CONFIRMED", "Confirmed"
        WAITLISTED = "WAITLISTED", "Waitlisted"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="led_team_registrations",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="team_registrations",
    )
    member_count = models.PositiveIntegerField()  # includes lead
    group_token = models.CharField(max_length=64, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=Status.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["created_at"]
    def __str__(self):
        return f"Team {self.group_token} → {self.event_id} ({self.status})"
    def save(self, *args, **kwargs):
        if not self.group_token:
            self.group_token = secrets.token_urlsafe(24)
        super().save(*args, **kwargs)

# Create your models here.
