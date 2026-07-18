from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOrganiser

from .models import Ticket
from .serializers import TicketCheckInSerializer, TicketSerializer
from rest_framework import generics

@extend_schema(tags=["Tickets"], summary="Check in a ticket")
class TicketCheckInView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated, IsOrganiser]
    serializer_class = TicketCheckInSerializer
    queryset = Ticket.objects.all()

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        if ticket.registration.event.organiser_id != request.user.id:
            return Response(
                {"detail": "You can only check in tickets for your own events."},
                status=status.HTTP_403_FORBIDDEN,
            )

            if ticket.status == Ticket.Status.CANCELLED:
                return Response(
                    {"detail": "Cancelled tickets cannot be checked in."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Idempotent: already USED → still 200
            if ticket.status == Ticket.Status.USED:
                return Response(TicketSerializer(ticket).data, status=status.HTTP_200_OK)

            # CONFIRMED → USED
            ticket.status = Ticket.Status.USED
            ticket.checked_in_at = timezone.now()
            ticket.save(update_fields=["status", "checked_in_at", "updated_at"])

        return Response(TicketSerializer(ticket).data, status=status.HTTP_200_OK)