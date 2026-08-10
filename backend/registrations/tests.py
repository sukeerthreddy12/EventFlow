from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from events.models import Event
from registrations.models import Registration
from tickets.models import Ticket


@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class RegistrationFlowTests(APITestCase):
    def setUp(self):
        # Organiser owns the event; two attendees compete for 1 seat
        self.org = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="pass12345",
            role=User.Role.ORGANISER,
            is_verified=True,
        )
        self.a1 = User.objects.create_user(
            username="a1",
            email="a1@test.com",
            password="pass12345",
            role=User.Role.ATTENDEE,
            is_verified=True,
        )
        self.a2 = User.objects.create_user(
            username="a2",
            email="a2@test.com",
            password="pass12345",
            role=User.Role.ATTENDEE,
            is_verified=True,
        )
        starts = timezone.now() + timedelta(days=2)
        self.event = Event.objects.create(
            title="Tiny Cap",
            description="t",
            venue="Hall",
            starts_at=starts,
            ends_at=starts + timedelta(hours=2),
            max_capacity=1,  # important: only one confirmed seat
            price=0,
            status=Event.Status.PUBLISHED,
            organiser=self.org,
        )

    def test_register_confirmed_then_waitlist(self):
        # a1 takes the only seat → CONFIRMED + ticket issued
        self.client.force_authenticate(self.a1)
        r1 = self.client.post(
            "/api/registrations/",
            {"event_id": str(self.event.id)},
            format="json",
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r1.data["status"], Registration.Status.CONFIRMED)
        self.assertTrue(Ticket.objects.filter(registration_id=r1.data["id"]).exists())

        # a2 arrives when full → WAITLISTED (no oversell)
        self.client.force_authenticate(self.a2)
        r2 = self.client.post(
            "/api/registrations/",
            {"event_id": str(self.event.id)},
            format="json",
        )
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.data["status"], Registration.Status.WAITLISTED)

    def test_cancel_promotes_waitlisted(self):
        self.client.force_authenticate(self.a1)
        r1 = self.client.post(
            "/api/registrations/",
            {"event_id": str(self.event.id)},
            format="json",
        )
        self.client.force_authenticate(self.a2)
        r2 = self.client.post(
            "/api/registrations/",
            {"event_id": str(self.event.id)},
            format="json",
        )

        # a1 cancels → a2 should be promoted in the same flow
        self.client.force_authenticate(self.a1)
        cancel = self.client.post(f"/api/registrations/{r1.data['id']}/cancel/")
        self.assertEqual(cancel.status_code, status.HTTP_200_OK)

        wait = Registration.objects.get(pk=r2.data["id"])
        self.assertEqual(wait.status, Registration.Status.CONFIRMED)