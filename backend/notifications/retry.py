from datetime import timedelta

from django.utils import timezone

from accounts.models import User
from events.models import Event

from .emails import (
    send_event_cancelled_email,
    send_event_reminder_email,
    send_registration_confirmed_email,
    send_waitlist_joined_email,
    send_waitlist_promoted_email,
)
from .models import EmailRetryQueue

SENDERS = {
    EmailRetryQueue.Kind.REGISTRATION_CONFIRMED: send_registration_confirmed_email,
    EmailRetryQueue.Kind.WAITLIST_JOINED: send_waitlist_joined_email,
    EmailRetryQueue.Kind.WAITLIST_PROMOTED: send_waitlist_promoted_email,
    EmailRetryQueue.Kind.EVENT_CANCELLED: send_event_cancelled_email,
    EmailRetryQueue.Kind.EVENT_REMINDER: send_event_reminder_email,
}


def enqueue_email_retry(
    kind: str,
    user: User,
    event: Event,
    error: Exception,
    *,
    delay_seconds: int = 60,
) -> EmailRetryQueue:
    return EmailRetryQueue.objects.create(
        kind=kind,
        user=user,
        event=event,
        status=EmailRetryQueue.Status.PENDING,
        attempts=0,
        last_error=str(error)[:2000],
        next_attempt_at=timezone.now() + timedelta(seconds=delay_seconds),
    )


def send_or_queue(kind: str, user: User, event: Event) -> None:
    """Try SMTP once; on failure persist a retry row instead of crashing loudly forever."""
    sender = SENDERS[kind]
    try:
        sender(user, event)
    except Exception as exc:
        enqueue_email_retry(kind, user, event, exc)
        # optional: re-raise if you still want Celery to mark the task failed
        # raise
        return


def attempt_retry_row(row: EmailRetryQueue) -> bool:
    """Returns True if sent."""
    sender = SENDERS[row.kind]
    user = row.user
    event = row.event
    try:
        sender(user, event)
    except Exception as exc:
        row.attempts += 1
        row.last_error = str(exc)[:2000]
        if row.attempts >= row.max_attempts:
            row.status = EmailRetryQueue.Status.DEAD
        else:
            # simple backoff: 1m, 2m, 4m, 8m...
            delay = 60 * (2 ** (row.attempts - 1))
            row.next_attempt_at = timezone.now() + timedelta(seconds=delay)
        row.save(
            update_fields=[
                "attempts",
                "last_error",
                "status",
                "next_attempt_at",
                "updated_at",
            ]
        )
        return False

    row.status = EmailRetryQueue.Status.SENT
    row.attempts += 1
    row.last_error = ""
    row.save(update_fields=["status", "attempts", "last_error", "updated_at"])
    return True