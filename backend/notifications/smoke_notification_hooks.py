"""
Smoke: registration / waitlist / promote / event-cancel email hooks.

Uses eager Celery + locmem email (no worker needed).

    cd backend
    uv run python notifications/smoke_notification_hooks.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

import django

django.setup()

from django.conf import settings  # noqa: E402

# Run tasks in-process; capture emails in memory (before importing mail)
settings.CELERY_TASK_ALWAYS_EAGER = True
settings.CELERY_TASK_EAGER_PROPAGATES = True
settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]

from django.core import mail  # noqa: E402
from django.utils import timezone  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from accounts.models import User  # noqa: E402
from backend.celery import app as celery_app  # noqa: E402
from events.models import Event  # noqa: E402
from registrations.models import Registration  # noqa: E402

celery_app.conf.task_always_eager = True
celery_app.conf.task_eager_propagates = True

PASSWORD = "testpass123"
passed = 0
failed = 0


def ok(label: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failed += 1
        extra = f" — {detail}" if detail else ""
        print(f"  FAIL  {label}{extra}")


def make_user(prefix: str, role: str = User.Role.ATTENDEE) -> User:
    suffix = uuid.uuid4().hex[:8]
    user = User(
        username=f"{prefix}_{suffix}",
        email=f"{prefix}_{suffix}@smoke.test",
        role=role,
        is_verified=True,
    )
    user.set_password(PASSWORD)
    user.save()
    return user


def client_for(user: User) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def create_event(organiser: User, capacity: int) -> Event:
    now = timezone.now()
    return Event.objects.create(
        title=f"Notify Smoke {uuid.uuid4().hex[:6]}",
        description="notification hook smoke",
        venue="Hall",
        starts_at=now + timedelta(days=7),
        ends_at=now + timedelta(days=7, hours=2),
        max_capacity=capacity,
        price=0,
        status=Event.Status.PUBLISHED,
        organiser=organiser,
    )


def subjects() -> list[str]:
    return [m.subject for m in getattr(mail, "outbox", [])]


def clear_mail() -> None:
    if not hasattr(mail, "outbox"):
        mail.outbox = []
    else:
        mail.outbox.clear()


def test_1_confirm_email() -> None:
    print("\n=== 1) Register -> confirmed email ===")
    clear_mail()
    org = make_user("org1", User.Role.ORGANISER)
    event = create_event(org, capacity=5)
    attendee = make_user("a1")

    resp = client_for(attendee).post(
        "/api/registrations/",
        {"event_id": str(event.id)},
        format="json",
    )
    ok("register 201 CONFIRMED", resp.status_code == 201 and resp.data.get("status") == "CONFIRMED", str(resp.data))
    ok(
        "confirmed email sent",
        any(s.startswith("Registration confirmed:") for s in subjects()),
        str(subjects()),
    )


def test_2_waitlist_email() -> None:
    print("\n=== 2) Register -> waitlist email ===")
    clear_mail()
    org = make_user("org2", User.Role.ORGANISER)
    event = create_event(org, capacity=1)
    a = make_user("fill")
    b = make_user("wait")

    r1 = client_for(a).post("/api/registrations/", {"event_id": str(event.id)}, format="json")
    ok("A confirmed", r1.status_code == 201 and r1.data.get("status") == "CONFIRMED")

    clear_mail()
    r2 = client_for(b).post("/api/registrations/", {"event_id": str(event.id)}, format="json")
    ok("B waitlisted", r2.status_code == 201 and r2.data.get("status") == "WAITLISTED", str(r2.data))
    ok(
        "waitlist email sent",
        any(s.startswith("Waitlisted:") for s in subjects()),
        str(subjects()),
    )


def test_3_cancel_promote_email() -> None:
    print("\n=== 3) Cancel -> promote email ===")
    clear_mail()
    org = make_user("org3", User.Role.ORGANISER)
    event = create_event(org, capacity=1)
    a = make_user("user_a")
    b = make_user("user_b")

    r_a = client_for(a).post("/api/registrations/", {"event_id": str(event.id)}, format="json")
    ok("A confirmed", r_a.status_code == 201 and r_a.data.get("status") == "CONFIRMED")
    r_b = client_for(b).post("/api/registrations/", {"event_id": str(event.id)}, format="json")
    ok("B waitlisted", r_b.status_code == 201 and r_b.data.get("status") == "WAITLISTED")

    clear_mail()
    a_reg_id = r_a.data["id"]
    cancel = client_for(a).post(f"/api/registrations/{a_reg_id}/cancel/", format="json")
    ok("A cancel 200", cancel.status_code == 200, str(cancel.data))

    b_reg = Registration.objects.get(event=event, user=b)
    ok("B now CONFIRMED", b_reg.status == Registration.Status.CONFIRMED, b_reg.status)
    ok(
        "promoted email sent",
        any(s.startswith("You're in:") for s in subjects()),
        str(subjects()),
    )


def test_4_event_cancel_emails() -> None:
    print("\n=== 4) Event cancel -> cancelled emails ===")
    clear_mail()
    org = make_user("org4", User.Role.ORGANISER)
    event = create_event(org, capacity=5)
    u1 = make_user("r1")
    u2 = make_user("r2")

    client_for(u1).post("/api/registrations/", {"event_id": str(event.id)}, format="json")
    client_for(u2).post("/api/registrations/", {"event_id": str(event.id)}, format="json")

    clear_mail()
    resp = client_for(org).post(f"/api/events/{event.id}/cancel/", format="json")
    ok("event cancel 200", resp.status_code == 200 and resp.data.get("status") == "CANCELLED", str(resp.data))

    cancelled_mails = [s for s in subjects() if s.startswith("Event cancelled:")]
    ok("two cancel emails", len(cancelled_mails) == 2, f"got {len(cancelled_mails)}: {subjects()}")


if __name__ == "__main__":
    print("Notification hooks smoke (eager Celery + locmem email)")
    try:
        test_1_confirm_email()
        test_2_waitlist_email()
        test_3_cancel_promote_email()
        test_4_event_cancel_emails()
    except Exception as exc:
        failed += 1
        print(f"\n  ERROR  {exc!r}")
        raise
    finally:
        print(f"\n=== Done: {passed} passed, {failed} failed ===")
        sys.exit(1 if failed else 0)
