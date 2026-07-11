import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        ORGANISER = "ORGANISER", "Organiser"
        ATTENDEE = "ATTENDEE", "Attendee"

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ATTENDEE)
    is_verified = models.BooleanField(default=False)
