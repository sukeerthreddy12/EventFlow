"""
Smoke: 24h reminder dispatcher.

    cd backend
    uv run python registrations/smoke_team_cancel_promote.py
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django

django.setup()

from django.utils import timezone
from accounts.models import User
from events.models import Event
from registrations.models import Registration
from tickets.services import issue_ticket
from notifications.tasks import dispatch_upcoming_event_reminders

org = User.objects.filter(role="ORGANISER").first()
attendee = (
    User.objects.filter(role="ATTENDEE", is_verified=True)
    .exclude(id=org.id)
    .first()
)

if org is None or attendee is None:
    raise SystemExit("Need at least one ORGANISER and one verified ATTENDEE in DB.")

starts = timezone.now() + timedelta(hours=24)
event = Event.objects.create(
    title="Reminder Smoke",
    description="beat test",
    venue="Test Hall",
    starts_at=starts,
    ends_at=starts + timedelta(hours=2),
    max_capacity=10,
    price=0,
    status=Event.Status.PUBLISHED,
    organiser=org,
)
reg = Registration.objects.create(
    user=attendee,
    event=event,
    status=Registration.Status.CONFIRMED,
)
issue_ticket(reg)

print("queued", dispatch_upcoming_event_reminders())
reg.refresh_from_db()
print("reminder_sent_at", reg.reminder_sent_at)

# second run should queue 0
print("queued again", dispatch_upcoming_event_reminders())