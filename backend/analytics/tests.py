from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from events.models import Event


class AnalyticsAuthTests(APITestCase):
    def setUp(self):
        self.org = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="pass12345",
            role=User.Role.ORGANISER,
            is_verified=True,
        )
        self.attendee = User.objects.create_user(
            username="att",
            email="att@test.com",
            password="pass12345",
            role=User.Role.ATTENDEE,
            is_verified=True,
        )
        starts = timezone.now() + timedelta(days=1)
        Event.objects.create(
            title="A",
            description="",
            venue="V",
            starts_at=starts,
            ends_at=starts + timedelta(hours=1),
            max_capacity=10,
            price="10.00",
            status=Event.Status.PUBLISHED,
            organiser=self.org,
        )

    def test_organiser_summary_ok(self):
        self.client.force_authenticate(self.org)
        res = self.client.get("/api/analytics/organiser/summary/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("events", res.data)
        self.assertEqual(res.data["event_count"], 1)

    def test_attendee_forbidden(self):
        self.client.force_authenticate(self.attendee)
        res = self.client.get("/api/analytics/organiser/summary/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)