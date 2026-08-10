from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from events.models import Event
from registrations.models import Registration
from tickets.models import Ticket
from tickets.services import issue_ticket


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class CheckInTests(APITestCase):
    def setUp(self):
        self.org = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="pass12345",
            role=User.Role.ORGANISER,
            is_verified=True,
        )
        self.other_org = User.objects.create_user(
            username="org2",
            email="org2@test.com",
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
        self.event = Event.objects.create(
            title="Show",
            description="",
            venue="V",
            starts_at=starts,
            ends_at=starts + timedelta(hours=2),
            max_capacity=10,
            price=0,
            status=Event.Status.PUBLISHED,
            organiser=self.org,
        )
        self.reg = Registration.objects.create(
            user=self.attendee,
            event=self.event,
            status=Registration.Status.CONFIRMED,
        )
        self.ticket = issue_ticket(self.reg)

    def test_organiser_check_in(self):
        self.client.force_authenticate(self.org)
        res = self.client.post(
            "/api/tickets/check-in/",
            {"token": self.ticket.token},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, Ticket.Status.USED)

    def test_idempotent_check_in(self):
        self.client.force_authenticate(self.org)
        self.client.post(
            "/api/tickets/check-in/",
            {"token": self.ticket.token},
            format="json",
        )
        res = self.client.post(
            "/api/tickets/check-in/",
            {"token": self.ticket.token},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_other_organiser_forbidden(self):
        self.client.force_authenticate(self.other_org)
        res = self.client.post(
            "/api/tickets/check-in/",
            {"token": self.ticket.token},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)