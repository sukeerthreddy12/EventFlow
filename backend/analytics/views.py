from decimal import Decimal

from django.db.models import Count, Q, Sum, F, DecimalField, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOrganiser
from events.models import Event
from registrations.models import Registration
from tickets.models import Ticket


def event_stats_qs(organiser):
    """Annotate organiser events with reg/check-in aggregates."""
    return (
        Event.objects.filter(organiser=organiser, is_deleted=False)
        .annotate(
            confirmed_count=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.CONFIRMED),
            ),
            waitlisted_count=Count(
                "registrations",
                filter=Q(registrations__status=Registration.Status.WAITLISTED),
            ),
            checked_in_count=Count(
                "registrations__ticket",
                filter=Q(registrations__ticket__status=Ticket.Status.USED),
            ),
        )
        .order_by("-starts_at")
    )


def serialize_event_stats(event) -> dict:
    confirmed = event.confirmed_count
    checked_in = event.checked_in_count
    rate = (checked_in / confirmed) if confirmed else 0.0
    revenue = (event.price or Decimal("0")) * confirmed
    return {
        "event_id": str(event.id),
        "title": event.title,
        "status": event.status,
        "starts_at": event.starts_at,
        "max_capacity": event.max_capacity,
        "confirmed_count": confirmed,
        "waitlisted_count": event.waitlisted_count,
        "checked_in_count": checked_in,
        "check_in_rate": round(rate, 4),
        "revenue": str(revenue),
    }


@extend_schema(tags=["Analytics"], summary="My organiser analytics summary")
class OrganiserAnalyticsSummaryView(APIView):
    permission_classes = [IsAuthenticated, IsOrganiser]

    def get(self, request):
        events = list(event_stats_qs(request.user))
        per_event = [serialize_event_stats(e) for e in events]
        total_confirmed = sum(e["confirmed_count"] for e in per_event)
        total_waitlisted = sum(e["waitlisted_count"] for e in per_event)
        total_checked_in = sum(e["checked_in_count"] for e in per_event)
        total_revenue = sum(Decimal(e["revenue"]) for e in per_event)
        overall_rate = (
            (total_checked_in / total_confirmed) if total_confirmed else 0.0
        )
        return Response(
            {
                "event_count": len(per_event),
                "total_confirmed": total_confirmed,
                "total_waitlisted": total_waitlisted,
                "total_checked_in": total_checked_in,
                "overall_check_in_rate": round(overall_rate, 4),
                "total_revenue": str(total_revenue),
                "events": per_event,
            }
        )


@extend_schema(tags=["Analytics"], summary="Analytics for one of my events")
class EventAnalyticsDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOrganiser]

    def get(self, request, pk):
        event = get_object_or_404(event_stats_qs(request.user), pk=pk)
        return Response(serialize_event_stats(event))