from celery import shared_task
from django.utils import timezone

from .models import Event


@shared_task
def advance_event_statuses() -> dict:
    """
    Flip PUBLISHED → ONGOING → COMPLETED from wall-clock time.
    Also archive past DRAFT events as COMPLETED (never auto-publish drafts).
    COMPLETED runs first so a late Beat tick does not briefly mark ended events ONGOING.
    """
    now = timezone.now()

    # Past-ended: PUBLISHED / ONGOING / DRAFT → COMPLETED
    completed = Event.objects.filter(
        is_deleted=False,
        status__in=[
            Event.Status.PUBLISHED,
            Event.Status.ONGOING,
            Event.Status.DRAFT,
        ],
        ends_at__lte=now,
    ).update(status=Event.Status.COMPLETED, updated_at=now)

    # Only already-published events can become ONGOING
    ongoing = Event.objects.filter(
        is_deleted=False,
        status=Event.Status.PUBLISHED,
        starts_at__lte=now,
        ends_at__gt=now,
    ).update(status=Event.Status.ONGOING, updated_at=now)

    return {"ongoing": ongoing, "completed": completed}