from django.conf import settings
from django.core.mail import send_mail

from accounts.models import User
from events.models import Event


def send_registration_confirmed_email(user: User, event: Event) -> None:
    send_mail(
        subject=f"Registration confirmed: {event.title}",
        message=(
            f"Hi {user.username},\n\n"
            f"You're confirmed for {event.title}.\n"
            f"Venue: {event.venue}\n"
            f"Starts: {event.starts_at}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_waitlist_joined_email(user: User, event: Event) -> None:
    send_mail(
        subject=f"Waitlisted: {event.title}",
        message=(
            f"Hi {user.username},\n\n"
            f"{event.title} is full. You're on the waitlist.\n"
            f"We'll email you if a seat opens.\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_waitlist_promoted_email(user: User, event: Event) -> None:
    send_mail(
        subject=f"You're in: {event.title}",
        message=(
            f"Hi {user.username},\n\n"
            f"A seat opened for {event.title}. You're now confirmed.\n"
            f"Venue: {event.venue}\n"
            f"Starts: {event.starts_at}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_event_cancelled_email(user: User, event: Event) -> None:
    send_mail(
        subject=f"Event cancelled: {event.title}",
        message=(
            f"Hi {user.username},\n\n"
            f"{event.title} has been cancelled.\n"
            f"Refund eligible: {'yes' if event.refund_eligible else 'no'}.\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def send_event_reminder_email(user: User, event: Event) -> None:
    send_mail(
        subject=f"Reminder: {event.title} is tomorrow",
        message=(
            f"Hi {user.username},\n\n"
            f"This is a reminder that {event.title} starts in about 24 hours.\n"
            f"Venue: {event.venue}\n"
            f"Starts: {event.starts_at}\n"
            f"Ends: {event.ends_at}\n"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )