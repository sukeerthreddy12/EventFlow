from celery import shared_task

from accounts.models import User
from events.models import Event

from .emails import (
    send_event_cancelled_email,
    send_registration_confirmed_email,
    send_waitlist_joined_email,
    send_waitlist_promoted_email,
)


@shared_task
def ping():
    print("pong from celery worker")
    return "pong"


@shared_task
def send_registration_confirmed_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_registration_confirmed_email(user, event)


@shared_task
def send_waitlist_joined_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_waitlist_joined_email(user, event)


@shared_task
def send_waitlist_promoted_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_waitlist_promoted_email(user, event)


@shared_task
def send_event_cancelled_task(user_id: str, event_id: str) -> None:
    user = User.objects.get(pk=user_id)
    event = Event.objects.get(pk=event_id)
    send_event_cancelled_email(user, event)