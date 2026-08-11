from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from events.models import Event
from registrations.models import Registration
from tickets.services import issue_ticket


DEMO_PASSWORD = "DemoPass123!"


class Command(BaseCommand):
    help = "Seed demo organiser, attendees, events, and sample registrations"

    def handle(self, *args, **options):
        org = self._upsert_user(
            email="organiser@demo.com",
            username="demo_organiser",
            role=User.Role.ORGANISER,
        )
        attendee = self._upsert_user(
            email="attendee@demo.com",
            username="demo_attendee",
            role=User.Role.ATTENDEE,
        )
        mate = self._upsert_user(
            email="teammate@demo.com",
            username="demo_teammate",
            role=User.Role.ATTENDEE,
        )
        # Hold the 2 Jazz seats — cancel one in the UI to auto-promote the waitlist
        seat_a = self._upsert_user(
            email="seat_a@demo.com",
            username="demo_seat_a",
            role=User.Role.ATTENDEE,
        )
        seat_b = self._upsert_user(
            email="seat_b@demo.com",
            username="demo_seat_b",
            role=User.Role.ATTENDEE,
        )
        # Second on Jazz waitlist — stays waitlisted when only one seat frees (FIFO)
        waitlist_b = self._upsert_user(
            email="waitlist_b@demo.com",
            username="demo_waitlist_b",
            role=User.Role.ATTENDEE,
        )

        # Extra attendees (not for login demos) — analytics volume
        fillers = [
            self._upsert_user(
                email=f"guest{i}@demo.com",
                username=f"demo_guest{i}",
                role=User.Role.ATTENDEE,
            )
            for i in range(1, 7)
        ]

        now = timezone.now()
        samples = [
            {
                "title": "Neon Night Market",
                "description": "Food, vinyl, and late doors. Featured catalog event.",
                "venue": "Harbor Hall",
                "starts_at": now + timedelta(days=3, hours=19),
                "ends_at": now + timedelta(days=3, hours=23),
                "max_capacity": 40,
                "price": Decimal("15.00"),
                "status": Event.Status.PUBLISHED,
                "is_featured": True,
            },
            {
                "title": "Rooftop Jazz",
                "description": "Tiny room — use this to demo waitlist / promote.",
                "venue": "Skyline Terrace",
                "starts_at": now + timedelta(days=5, hours=20),
                "ends_at": now + timedelta(days=5, hours=22),
                "max_capacity": 2,
                "price": Decimal("0"),
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
            },
            {
                "title": "Harbor Tech Meetup",
                "description": "Talks + networking. Good for team register demos.",
                "venue": "Pier 4 Loft",
                "starts_at": now + timedelta(days=7, hours=18),
                "ends_at": now + timedelta(days=7, hours=21),
                "max_capacity": 30,
                "price": Decimal("10.00"),
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
            },
            {
                "title": "Gallery After Hours",
                "description": "Walkthrough + drinks. Mid-size paid event.",
                "venue": "East Wing Gallery",
                "starts_at": now + timedelta(days=9, hours=19),
                "ends_at": now + timedelta(days=9, hours=22),
                "max_capacity": 25,
                "price": Decimal("20.00"),
                "status": Event.Status.PUBLISHED,
                "is_featured": True,
            },
            {
                "title": "Sunrise Yoga",
                "description": "Outdoor session. Free, moderate capacity.",
                "venue": "South Lawn",
                "starts_at": now + timedelta(days=4, hours=6),
                "ends_at": now + timedelta(days=4, hours=7, minutes=30),
                "max_capacity": 15,
                "price": Decimal("0"),
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
            },
            {
                "title": "Live Check-In Night",
                "description": "Seeded as ONGOING — demo organiser check-in + QR.",
                "venue": "Main Stage",
                "starts_at": now - timedelta(hours=1),
                "ends_at": now + timedelta(hours=3),
                "max_capacity": 50,
                "price": Decimal("12.00"),
                "status": Event.Status.ONGOING,
                "is_featured": False,
            },
            {
                "title": "Winter Lights (Past)",
                "description": "Completed event — shows up in organiser analytics.",
                "venue": "Riverwalk",
                "starts_at": now - timedelta(days=14, hours=18),
                "ends_at": now - timedelta(days=14, hours=22),
                "max_capacity": 60,
                "price": Decimal("18.00"),
                "status": Event.Status.COMPLETED,
                "is_featured": False,
            },
            {
                "title": "Draft Workshop",
                "description": "DRAFT — not in public catalog. Organiser-only.",
                "venue": "Studio B",
                "starts_at": now + timedelta(days=10, hours=18),
                "ends_at": now + timedelta(days=10, hours=20),
                "max_capacity": 20,
                "price": Decimal("25.00"),
                "status": Event.Status.DRAFT,
                "is_featured": False,
            },
            {
                "title": "Cancelled Mixer",
                "description": "CANCELLED — refund_eligible set for demo.",
                "venue": "Mezzanine",
                "starts_at": now + timedelta(days=6, hours=19),
                "ends_at": now + timedelta(days=6, hours=21),
                "max_capacity": 40,
                "price": Decimal("8.00"),
                "status": Event.Status.CANCELLED,
                "is_featured": False,
                "refund_eligible": True,
            },
        ]

        events = {}
        for data in samples:
            event, _ = Event.objects.update_or_create(
                title=data["title"],
                organiser=org,
                defaults={**data, "is_deleted": False, "is_suppressed": False},
            )
            events[data["title"]] = event

        # --- Registrations shaped for demos ---
        neon = events["Neon Night Market"]
        jazz = events["Rooftop Jazz"]
        meetup = events["Harbor Tech Meetup"]
        live = events["Live Check-In Night"]
        past = events["Winter Lights (Past)"]
        yoga = events["Sunrise Yoga"]

        # Attendee: confirmed on several; ticket ready for check-in on live event
        self._confirm(attendee, neon)
        self._confirm(attendee, meetup)
        self._confirm(attendee, live)
        self._confirm(attendee, past, mark_used=True)

        # Teammate: confirmed elsewhere + first on Jazz waitlist
        self._confirm(mate, neon)
        self._confirm(mate, yoga)  # partner for team-register demos

        # Rooftop Jazz (cap 2): reset active regs so reseed stays demo-shaped
        Registration.objects.filter(
            event=jazz,
            status__in=[
                Registration.Status.CONFIRMED,
                Registration.Status.WAITLISTED,
            ],
        ).update(status=Registration.Status.CANCELLED)
        self._confirm(seat_a, jazz)
        self._confirm(seat_b, jazz)
        self._waitlist(mate, jazz)  # first in line
        self._waitlist(waitlist_b, jazz)  # second in line

        # Fillers for analytics (confirmed + some checked in on past/live)
        for user in fillers[:3]:
            self._confirm(user, neon)
            self._confirm(user, past, mark_used=True)
        self._confirm(fillers[3], live, mark_used=True)

        self.stdout.write(self.style.SUCCESS("Demo seed complete."))
        self.stdout.write("")
        self.stdout.write("Login accounts (password for all: DemoPass123!)")
        self.stdout.write("  organiser@demo.com   — My Events, check-in, analytics, drafts")
        self.stdout.write("  attendee@demo.com    — catalog, tickets/QR, cancel")
        self.stdout.write("  teammate@demo.com    — 1st waitlisted on Rooftop Jazz")
        self.stdout.write("  seat_a@demo.com      — CONFIRMED on Rooftop Jazz (cancel to promote)")
        self.stdout.write("  seat_b@demo.com      — CONFIRMED on Rooftop Jazz")
        self.stdout.write("  waitlist_b@demo.com  — 2nd waitlisted on Rooftop Jazz")
        self.stdout.write("")
        self.stdout.write("Handy demo flows:")
        self.stdout.write("  • Catalog / register     → Neon Night Market, Harbor Tech Meetup")
        self.stdout.write("  • Waitlist / promote     → Rooftop Jazz:")
        self.stdout.write("      1) teammate@ = WAITLISTED")
        self.stdout.write("      2) login seat_a@ → cancel Jazz registration")
        self.stdout.write("      3) teammate@ becomes CONFIRMED (auto-promote); waitlist_b stays waitlisted")
        self.stdout.write("  • Check-in + QR          → Live Check-In Night (ONGOING)")
        self.stdout.write("  • Analytics              → Winter Lights (past) + seeded regs")
        self.stdout.write("  • Draft (organiser only) → Draft Workshop")
        self.stdout.write("  • Cancelled              → Cancelled Mixer")

    def _upsert_user(self, *, email: str, username: str, role: str) -> User:
        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": username,
                "role": role,
                "is_verified": True,
            },
        )
        user.set_password(DEMO_PASSWORD)
        user.save(update_fields=["password"])
        return user

    def _confirm(self, user: User, event: Event, *, mark_used: bool = False) -> None:
        reg, created = Registration.objects.get_or_create(
            user=user,
            event=event,
            defaults={"status": Registration.Status.CONFIRMED},
        )
        if not created and reg.status != Registration.Status.CONFIRMED:
            reg.status = Registration.Status.CONFIRMED
            reg.save(update_fields=["status", "updated_at"])

        ticket = issue_ticket(reg)
        if mark_used and ticket.status != ticket.Status.USED:
            ticket.status = ticket.Status.USED
            ticket.checked_in_at = timezone.now()
            ticket.save(update_fields=["status", "checked_in_at", "updated_at"])

    def _waitlist(self, user: User, event: Event) -> None:
        Registration.objects.update_or_create(
            user=user,
            event=event,
            defaults={"status": Registration.Status.WAITLISTED},
        )
