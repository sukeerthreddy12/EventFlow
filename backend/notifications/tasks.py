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