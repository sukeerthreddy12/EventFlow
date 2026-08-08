from celery import shared_task
from datetime import timedelta
from django.utils import timezone
from registrations.models import Registration
from .models import EmailRetryQueue
from .retry import attempt_retry_row, send_or_queue

from accounts.models import User
from events.models import Event


from .emails import (
    send_event_cancelled_email,
    send_registration_confirmed_email,
    send_waitlist_joined_email,
    send_waitlist_promoted_email,
    send_event_reminder_email,

)


@shared_task
def ping():
    print("pong from celery worker")
    return "pong"


@shared_task
def send_registration_confirmed_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_or_queue(EmailRetryQueue.Kind.REGISTRATION_CONFIRMED, user, event)


@shared_task
def send_waitlist_joined_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_or_queue(EmailRetryQueue.Kind.WAITLIST_JOINED, user, event)


@shared_task
def send_waitlist_promoted_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_or_queue(EmailRetryQueue.Kind.WAITLIST_PROMOTED, user, event)


@shared_task
def send_event_cancelled_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_or_queue(EmailRetryQueue.Kind.EVENT_CANCELLED, user, event)


@shared_task
def send_event_reminder_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_or_queue(EmailRetryQueue.Kind.EVENT_REMINDER, user, event)

@shared_task
def dispatch_upcoming_event_reminders() -> int:
    """
    Find CONFIRMED registrations for events starting ~24h from now
    and send one reminder each (idempotent via reminder_sent_at).
    Returns how many reminders were queued/sent this run.
    """
    now = timezone.now()
    window_start = now + timedelta(hours=23, minutes=45)
    window_end = now + timedelta(hours=24, minutes=15)

    qs = (
        Registration.objects.select_related("user", "event")
        .filter(
            status=Registration.Status.CONFIRMED,
            reminder_sent_at__isnull=True,
            event__starts_at__gte=window_start,
            event__starts_at__lt=window_end,
            event__status=Event.Status.PUBLISHED,
            event__is_deleted=False,
        )
    )

    sent = 0
    for reg in qs.iterator():
        send_or_queue(
            EmailRetryQueue.Kind.EVENT_REMINDER,
            reg.user,
            reg.event,
        )
        reg.reminder_sent_at = now
        reg.save(update_fields=["reminder_sent_at", "updated_at"])
        sent += 1

    return sent

@shared_task
def process_email_retry_queue(limit: int = 50) -> int:
    """
    Retry due PENDING rows. Returns number successfully sent this run.
    """
    now = timezone.now()
    rows = (
        EmailRetryQueue.objects.select_related("user", "event")
        .filter(
            status=EmailRetryQueue.Status.PENDING,
            next_attempt_at__lte=now,
        )
        .order_by("next_attempt_at")[:limit]
    )
    sent = 0
    for row in rows:
        if attempt_retry_row(row):
            sent += 1
    return sent