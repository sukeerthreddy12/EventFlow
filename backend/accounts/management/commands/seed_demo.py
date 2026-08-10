from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from events.models import Event


class Command(BaseCommand):
    help = "Seed demo organiser, attendees, and sample events"

    def handle(self, *args, **options):
        org, created_org = User.objects.update_or_create(
            email="organiser@demo.com",
            defaults={
                "username": "demo_organiser",
                "role": User.Role.ORGANISER,
                "is_verified": True,
            },
        )
        org.set_password("DemoPass123!")
        org.save(update_fields=["password"])

        attendee, _ = User.objects.update_or_create(
            email="attendee@demo.com",
            defaults={
                "username": "demo_attendee",
                "role": User.Role.ATTENDEE,
                "is_verified": True,
            },
        )
        attendee.set_password("DemoPass123!")
        attendee.save(update_fields=["password"])

        mate, _ = User.objects.update_or_create(
            email="teammate@demo.com",
            defaults={
                "username": "demo_teammate",
                "role": User.Role.ATTENDEE,
                "is_verified": True,
            },
        )
        mate.set_password("DemoPass123!")
        mate.save(update_fields=["password"])

        now = timezone.now()
        samples = [
            {
                "title": "Neon Night Market",
                "description": "Food, vinyl, and late doors.",
                "venue": "Harbor Hall",
                "starts_at": now + timedelta(days=3, hours=19),
                "ends_at": now + timedelta(days=3, hours=23),
                "max_capacity": 40,
                "price": "15.00",
                "status": Event.Status.PUBLISHED,
                "is_featured": True,
            },
            {
                "title": "Rooftop Jazz",
                "description": "Small capacity — waitlist friendly.",
                "venue": "Skyline Terrace",
                "starts_at": now + timedelta(days=5, hours=20),
                "ends_at": now + timedelta(days=5, hours=22),
                "max_capacity": 8,
                "price": "0",
                "status": Event.Status.PUBLISHED,
                "is_featured": False,
            },
            {
                "title": "Draft Workshop",
                "description": "Not visible in public catalog.",
                "venue": "Studio B",
                "starts_at": now + timedelta(days=10, hours=18),
                "ends_at": now + timedelta(days=10, hours=20),
                "max_capacity": 20,
                "price": "25.00",
                "status": Event.Status.DRAFT,
                "is_featured": False,
            },
        ]

        for data in samples:
            Event.objects.update_or_create(
                title=data["title"],
                organiser=org,
                defaults={**data, "is_deleted": False},
            )

        self.stdout.write(self.style.SUCCESS("Demo seed complete."))
        self.stdout.write("organiser@demo.com / DemoPass123!")
        self.stdout.write("attendee@demo.com  / DemoPass123!")
        self.stdout.write("teammate@demo.com  / DemoPass123!")
        if created_org:
            self.stdout.write("(organiser account was newly created)")
