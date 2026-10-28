"""
Concurrency test: 10 attendees race for the last seat of an event.

Run from the backend folder (Postgres must be running):
    docker compose up -d postgres
    python manage.py test registrations.test_concurrency -v 2

Expected: exactly 1 CONFIRMED, 9 WAITLISTED, 1 ticket.

Prove the test is real: comment out `.select_for_update()` in
RegistrationListCreateView._register (registrations/views.py) and run again.
It should FAIL with more than 1 CONFIRMED. Then put the lock back.
"""
import threading
from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from events.models import Event
from registrations.models import Registration
from tickets.models import Ticket

N_THREADS = 10


class RegistrationRaceTest(TransactionTestCase):
    # TransactionTestCase, not TestCase / APITestCase:
    # TestCase wraps the whole test in ONE transaction and rolls it back,
    # so the users and event created in setUp are never committed, and the
    # other threads (each with its own DB connection) could not see them.
    # TransactionTestCase really commits, then truncates tables after the test.

    def setUp(self):
        self.org = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="pass12345",
            role=User.Role.ORGANISER,
            is_verified=True,
        )
        self.attendees = [
            User.objects.create_user(
                username=f"a{i}",
                email=f"a{i}@test.com",
                password="pass12345",
                role=User.Role.ATTENDEE,
                is_verified=True,
            )
            for i in range(N_THREADS)
        ]
        starts = timezone.now() + timedelta(days=2)
        self.event = Event.objects.create(
            title="Last seat",
            description="race test",
            venue="Hall",
            starts_at=starts,
            ends_at=starts + timedelta(hours=2),
            max_capacity=1,  # only one seat
            price=0,
            status=Event.Status.PUBLISHED,
            organiser=self.org,
        )

    # In a TransactionTestCase the transaction really commits, so
    # transaction.on_commit callbacks really fire and would call .delay(),
    # which needs Redis. Replace the tasks with mocks: this test is about
    # seats, not emails.
    @patch("registrations.views.send_waitlist_joined_task")
    @patch("registrations.views.send_registration_confirmed_task")
    def test_ten_attendees_race_for_one_seat(self, confirmed_task, waitlist_task):
        barrier = threading.Barrier(N_THREADS)  # release all threads together
        status_codes = []
        errors = []

        def register(user):
            try:
                client = APIClient()
                client.force_authenticate(user=user)  # skip JWT login
                barrier.wait()
                resp = client.post(
                    "/api/registrations/",
                    {"event_id": str(self.event.id)},
                    format="json",
                )
                status_codes.append(resp.status_code)
            except Exception as exc:  # a crashed thread must fail the test
                errors.append(exc)
            finally:
                # Each thread opened its own DB connection. Close it, or the
                # test database can't be dropped at the end of the run.
                connection.close()

        threads = [threading.Thread(target=register, args=(u,)) for u in self.attendees]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Every request finished and succeeded
        self.assertEqual(errors, [])
        self.assertEqual(sorted(status_codes), [201] * N_THREADS)

        # The real assertion: no overselling
        regs = Registration.objects.filter(event=self.event)
        self.assertEqual(regs.filter(status=Registration.Status.CONFIRMED).count(), 1)
        self.assertEqual(
            regs.filter(status=Registration.Status.WAITLISTED).count(), N_THREADS - 1
        )
        self.assertEqual(Ticket.objects.filter(registration__event=self.event).count(), 1)

        # Emails were queued after commit: 1 confirmation, 9 waitlist
        self.assertEqual(confirmed_task.delay.call_count, 1)
        self.assertEqual(waitlist_task.delay.call_count, N_THREADS - 1)
