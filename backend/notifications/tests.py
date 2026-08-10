from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from events.models import Event
from registrations.models import Registration

from .models import EmailRetryQueue
from .tasks import dispatch_upcoming_event_reminders, process_email_retry_queue


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ReminderDispatcherTests(TestCase):
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
        starts = timezone.now() + timedelta(hours=24)
        self.event = Event.objects.create(
            title="Soon",
            description="",
            venue="Hall",
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

    @patch("notifications.tasks.send_or_queue")
    def test_dispatch_sends_once_and_sets_flag(self, mock_send):
        sent = dispatch_upcoming_event_reminders()
        self.assertEqual(sent, 1)
        mock_send.assert_called_once()
        self.reg.refresh_from_db()
        self.assertIsNotNone(self.reg.reminder_sent_at)

        # Idempotent: second Beat tick should not re-send
        sent_again = dispatch_upcoming_event_reminders()
        self.assertEqual(sent_again, 0)
        self.assertEqual(mock_send.call_count, 1)

    @patch("notifications.tasks.send_or_queue")
    def test_dispatch_skips_waitlisted(self, mock_send):
        self.reg.status = Registration.Status.WAITLISTED
        self.reg.save(update_fields=["status"])

        sent = dispatch_upcoming_event_reminders()
        self.assertEqual(sent, 0)
        mock_send.assert_not_called()


@override_settings(
    CELERY_TASK_ALWAYS_EAGER=True,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class EmailRetryQueueTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="u",
            email="u@test.com",
            password="pass12345",
            role=User.Role.ATTENDEE,
            is_verified=True,
        )
        self.org = User.objects.create_user(
            username="org",
            email="org@test.com",
            password="pass12345",
            role=User.Role.ORGANISER,
            is_verified=True,
        )
        starts = timezone.now() + timedelta(days=2)
        self.event = Event.objects.create(
            title="E",
            description="",
            venue="V",
            starts_at=starts,
            ends_at=starts + timedelta(hours=1),
            max_capacity=5,
            price=0,
            status=Event.Status.PUBLISHED,
            organiser=self.org,
        )
        self.row = EmailRetryQueue.objects.create(
            kind=EmailRetryQueue.Kind.EVENT_REMINDER,
            user=self.user,
            event=self.event,
            status=EmailRetryQueue.Status.PENDING,
            next_attempt_at=timezone.now() - timedelta(seconds=1),
            last_error="smtp down",
        )

    def test_process_retry_queue_marks_sent(self):
        # SENDERS holds function refs at import time — patch the dict entry.
        mock_sender = MagicMock()
        with patch.dict(
            "notifications.retry.SENDERS",
            {EmailRetryQueue.Kind.EVENT_REMINDER: mock_sender},
        ):
            sent = process_email_retry_queue()
        self.assertEqual(sent, 1)
        self.row.refresh_from_db()
        self.assertEqual(self.row.status, EmailRetryQueue.Status.SENT)
        mock_sender.assert_called_once_with(self.user, self.event)

    def test_process_retry_queue_keeps_pending_on_failure(self):
        mock_sender = MagicMock(side_effect=RuntimeError("still down"))
        with patch.dict(
            "notifications.retry.SENDERS",
            {EmailRetryQueue.Kind.EVENT_REMINDER: mock_sender},
        ):
            sent = process_email_retry_queue()
        self.assertEqual(sent, 0)
        self.row.refresh_from_db()
        self.assertEqual(self.row.status, EmailRetryQueue.Status.PENDING)
        self.assertEqual(self.row.attempts, 1)
