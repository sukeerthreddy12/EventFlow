"""
Smoke test: team cancel + waitlist promotion (no manual logins).

Run from backend/ with server NOT required (uses DRF APIClient):

    uv run python registrations/smoke_team_cancel_promote.py
"""

from __future__ import annotations

import os
import sys
import uuid
from datetime import timedelta
from pathlib import Path

import django

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402
from rest_framework.test import APIClient  # noqa: E402

from accounts.models import User  # noqa: E402
from events.models import Event  # noqa: E402
from registrations.models import Registration, TeamRegistration  # noqa: E402
from tickets.models import Ticket  # noqa: E402

# DRF APIClient uses host "testserver"
if "testserver" not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = [*settings.ALLOWED_HOSTS, "testserver"]

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
        title=f"Smoke {uuid.uuid4().hex[:6]}",
        description="team cancel/promote smoke",
        venue="Test Hall",
        starts_at=now + timedelta(days=7),
        ends_at=now + timedelta(days=7, hours=3),
        max_capacity=capacity,
        price=0,
        status=Event.Status.PUBLISHED,
        organiser=organiser,
    )


def team_register(lead: User, event_id, member_emails: list[str]):
    resp = client_for(lead).post(
        "/api/registrations/team/",
        {"event_id": str(event_id), "member_emails": member_emails},
        format="json",
    )
    return resp


def solo_register(user: User, event_id):
    return client_for(user).post(
        "/api/registrations/",
        {"event_id": str(event_id)},
        format="json",
    )


def cancel_reg(user: User, reg_id):
    return client_for(user).post(f"/api/registrations/{reg_id}/cancel/", format="json")


def statuses_for_users(event, users):
    return {
        u.email: Registration.objects.get(event=event, user=u).status for u in users
    }


def run_scenario_promote() -> None:
    print("\n=== Scenario A: capacity 3 — Team A confirm, B+C waitlist, cancel A ===")
    organiser = make_user("org_a", User.Role.ORGANISER)
    event = create_event(organiser, capacity=3)

    # Team A — 3 people
    a_lead = make_user("a_lead")
    a1 = make_user("a_m1")
    a2 = make_user("a_m2")
    resp_a = team_register(a_lead, event.id, [a1.email, a2.email])
    ok("A registers 201", resp_a.status_code == 201, str(resp_a.data))
    ok("A status CONFIRMED", resp_a.data.get("status") == "CONFIRMED", str(resp_a.data))
    ok("A member_count 3", resp_a.data.get("member_count") == 3, str(resp_a.data))

    # Team B — 2 people (waitlist)
    b_lead = make_user("b_lead")
    b1 = make_user("b_m1")
    resp_b = team_register(b_lead, event.id, [b1.email])
    ok("B registers 201", resp_b.status_code == 201, str(resp_b.data))
    ok("B status WAITLISTED", resp_b.data.get("status") == "WAITLISTED", str(resp_b.data))

    # Solo C — waitlist after B
    c = make_user("solo_c")
    resp_c = solo_register(c, event.id)
    ok("C registers 201", resp_c.status_code == 201, str(resp_c.data))
    ok("C status WAITLISTED", resp_c.data.get("status") == "WAITLISTED", str(resp_c.data))

    # Cancel one member of Team A → whole A cancelled; B then C promoted
    a_reg_id = resp_a.data["registrations"][0]["id"]
    # cancel as the owner of that registration
    cancel_user_id = resp_a.data["registrations"][0]["user"]
    cancel_user = User.objects.get(pk=cancel_user_id)
    resp_cancel = cancel_reg(cancel_user, a_reg_id)
    ok("Cancel A returns 200", resp_cancel.status_code == 200, str(resp_cancel.data))

    a_users = [a_lead, a1, a2]
    for u in a_users:
        reg = Registration.objects.get(event=event, user=u)
        ok(f"A member {u.email} CANCELLED", reg.status == Registration.Status.CANCELLED)

    team_a = TeamRegistration.objects.get(pk=resp_a.data["id"])
    ok("Team A CANCELLED", team_a.status == TeamRegistration.Status.CANCELLED)

    team_b = TeamRegistration.objects.get(pk=resp_b.data["id"])
    ok("Team B promoted CONFIRMED", team_b.status == TeamRegistration.Status.CONFIRMED)
    for u in [b_lead, b1]:
        reg = Registration.objects.get(event=event, user=u)
        ok(f"B member {u.email} CONFIRMED", reg.status == Registration.Status.CONFIRMED)
        ok(
            f"B member {u.email} has ticket",
            Ticket.objects.filter(registration=reg, status=Ticket.Status.CONFIRMED).exists(),
        )

    c_reg = Registration.objects.get(event=event, user=c)
    ok("Solo C promoted CONFIRMED", c_reg.status == Registration.Status.CONFIRMED)
    ok(
        "Solo C has ticket",
        Ticket.objects.filter(registration=c_reg, status=Ticket.Status.CONFIRMED).exists(),
    )


def run_scenario_skip_to_fit() -> None:
    """1 free seat; queue = Team(3) then Solo → skip team, promote solo."""
    print("\n=== Scenario B: skip-to-fit — Team D (3) then Solo E; cancel frees 1 ===")
    organiser = make_user("org_b", User.Role.ORGANISER)
    event = create_event(organiser, capacity=3)

    x = make_user("solo_x")
    y = make_user("solo_y")
    z = make_user("solo_z")
    for u in (x, y, z):
        r = solo_register(u, event.id)
        ok(
            f"{u.email} confirmed",
            r.status_code == 201 and r.data.get("status") == "CONFIRMED",
        )

    d_lead = make_user("d_lead")
    d1 = make_user("d_m1")
    d2 = make_user("d_m2")
    resp_d = team_register(d_lead, event.id, [d1.email, d2.email])
    ok(
        "D waitlisted first",
        resp_d.status_code == 201 and resp_d.data.get("status") == "WAITLISTED",
    )

    e = make_user("solo_e")
    resp_e = solo_register(e, event.id)
    ok(
        "E waitlisted after D",
        resp_e.status_code == 201 and resp_e.data.get("status") == "WAITLISTED",
    )

    # Cancel X → 1 free seat; skip Team D (needs 3), promote Solo E
    x_reg = Registration.objects.get(event=event, user=x)
    resp_cancel = cancel_reg(x, x_reg.id)
    ok("Cancel X 200", resp_cancel.status_code == 200, str(resp_cancel.data))

    team_d = TeamRegistration.objects.get(pk=resp_d.data["id"])
    ok(
        "Team D still WAITLISTED (skipped)",
        team_d.status == TeamRegistration.Status.WAITLISTED,
        team_d.status,
    )
    for u in [d_lead, d1, d2]:
        reg = Registration.objects.get(event=event, user=u)
        ok(
            f"D member still WAITLISTED ({u.email})",
            reg.status == Registration.Status.WAITLISTED,
        )

    e_reg = Registration.objects.get(event=event, user=e)
    ok("Solo E promoted CONFIRMED", e_reg.status == Registration.Status.CONFIRMED)
    ok(
        "Solo E has ticket",
        Ticket.objects.filter(
            registration=e_reg, status=Ticket.Status.CONFIRMED
        ).exists(),
    )

    confirmed = Registration.objects.filter(
        event=event, status=Registration.Status.CONFIRMED
    ).count()
    ok("Confirmed count is 3 (Y, Z, E)", confirmed == 3, f"got {confirmed}")


def run_scenario_nobody_fits() -> None:
    """1 free seat; only Team(3) waitlisted → nobody promoted."""
    print("\n=== Scenario C: nobody fits — only Team F (3) waitlisted; cancel frees 1 ===")
    organiser = make_user("org_c", User.Role.ORGANISER)
    event = create_event(organiser, capacity=3)

    x = make_user("solo_x2")
    y = make_user("solo_y2")
    z = make_user("solo_z2")
    for u in (x, y, z):
        r = solo_register(u, event.id)
        ok(
            f"{u.email} confirmed",
            r.status_code == 201 and r.data.get("status") == "CONFIRMED",
        )

    f_lead = make_user("f_lead")
    f1 = make_user("f_m1")
    f2 = make_user("f_m2")
    resp_f = team_register(f_lead, event.id, [f1.email, f2.email])
    ok(
        "F waitlisted",
        resp_f.status_code == 201 and resp_f.data.get("status") == "WAITLISTED",
    )

    x_reg = Registration.objects.get(event=event, user=x)
    resp_cancel = cancel_reg(x, x_reg.id)
    ok("Cancel X 200", resp_cancel.status_code == 200, str(resp_cancel.data))

    team_f = TeamRegistration.objects.get(pk=resp_f.data["id"])
    ok(
        "Team F still WAITLISTED",
        team_f.status == TeamRegistration.Status.WAITLISTED,
        team_f.status,
    )
    confirmed = Registration.objects.filter(
        event=event, status=Registration.Status.CONFIRMED
    ).count()
    ok("Still exactly 2 confirmed (Y,Z)", confirmed == 2, f"got {confirmed}")


if __name__ == "__main__":
    print("Team cancel + promote smoke test (skip-to-fit)")
    print("(creates temporary users/events in your DB)")
    try:
        run_scenario_promote()
        run_scenario_skip_to_fit()
        run_scenario_nobody_fits()
    except Exception as exc:
        failed += 1
        print(f"\n  ERROR  {exc!r}")
        raise
    finally:
        print(f"\n=== Done: {passed} passed, {failed} failed ===")
        sys.exit(1 if failed else 0)
