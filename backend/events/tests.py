from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User

from .models import Event
from .tasks import advance_event_statuses


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AdvanceEventStatusesTests(TestCase):
    def setUp(self):
        self.org = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="pass12345",
            role=User.Role.ORGANISER,
            is_verified=True,
        )
        self.now = timezone.now()

    def _event(self, **kwargs):
        defaults = {
            "title": "E",
            "description": "",
            "venue": "V",
            "starts_at": self.now + timedelta(hours=1),
            "ends_at": self.now + timedelta(hours=3),
            "max_capacity": 10,
            "price": 0,
            "status": Event.Status.PUBLISHED,
            "organiser": self.org,
            "is_deleted": False,
        }
        defaults.update(kwargs)
        return Event.objects.create(**defaults)

    def test_published_becomes_ongoing(self):
        event = self._event(
            starts_at=self.now - timedelta(minutes=30),
            ends_at=self.now + timedelta(hours=2),
            status=Event.Status.PUBLISHED,
        )
        result = advance_event_statuses()
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.ONGOING)
        self.assertEqual(result["ongoing"], 1)

    def test_ended_published_becomes_completed(self):
        event = self._event(
            starts_at=self.now - timedelta(hours=3),
            ends_at=self.now - timedelta(minutes=5),
            status=Event.Status.PUBLISHED,
        )
        result = advance_event_statuses()
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.COMPLETED)
        self.assertEqual(result["completed"], 1)

    def test_past_draft_becomes_completed_not_published(self):
        event = self._event(
            starts_at=self.now - timedelta(hours=3),
            ends_at=self.now - timedelta(minutes=5),
            status=Event.Status.DRAFT,
        )
        advance_event_statuses()
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.COMPLETED)

    def test_live_draft_stays_draft(self):
        event = self._event(
            starts_at=self.now - timedelta(minutes=10),
            ends_at=self.now + timedelta(hours=2),
            status=Event.Status.DRAFT,
        )
        advance_event_statuses()
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.DRAFT)
