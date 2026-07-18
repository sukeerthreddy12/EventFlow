from django.shortcuts import render
from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .permissions import IsRegistrationOwner
from rest_framework.views import APIView
from tickets.services import cancel_ticket, issue_ticket

from accounts.permissions import IsAttendeeOrOrganiser
from events.models import Event

from .models import Registration
from .serializers import RegistrationCreateSerializer, RegistrationSerializer


@extend_schema_view(
    get=extend_schema(tags=["Registrations"], summary="List my registrations"),
    post=extend_schema(tags=["Registrations"], summary="Register for an event"),
)
class RegistrationListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsAttendeeOrOrganiser]

    def get_queryset(self):
        return Registration.objects.filter(user=self.request.user).select_related(
            "event"
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return RegistrationCreateSerializer
        return RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.context["event"]

        try:
            registration = self._register(request.user, event)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            RegistrationSerializer(registration).data,
            status=status.HTTP_201_CREATED,
        )

    def _register(self, user, event):
        with transaction.atomic():
            # Lock the event row so concurrent registers can't oversell
            locked_event = (
                Event.objects.select_for_update()
                .filter(pk=event.pk, is_deleted=False)
                .first()
            )
            if locked_event is None:
                raise ValueError("Event not found.")

            if locked_event.status != Event.Status.PUBLISHED:
                raise ValueError("Only PUBLISHED events can be registered for.")

            if locked_event.organiser_id == user.id:
                raise ValueError("You cannot register for your own event.")
            

            # Re-check duplicate inside the lock
            if Registration.objects.filter(
                user=user,
                event=locked_event,
                status__in=[
                    Registration.Status.CONFIRMED,
                    Registration.Status.WAITLISTED,
                ],
            ).exists():
                raise ValueError(
                    "You already have an active registration for this event."
                )

            confirmed_count = Registration.objects.filter(
                event=locked_event,
                status=Registration.Status.CONFIRMED,
            ).count()

            if confirmed_count < locked_event.max_capacity:
                new_status = Registration.Status.CONFIRMED
            else:
                new_status = Registration.Status.WAITLISTED

            registration = Registration.objects.create( user=user,
                event=locked_event,
                status=new_status,)

            if registration.status == Registration.Status.CONFIRMED:
                issue_ticket(registration)

            return registration

@extend_schema(tags=["Registrations"], summary="Cancel my registration")
class RegistrationCancelView(APIView):
    permission_classes = [IsAuthenticated, IsRegistrationOwner]

    def get_object(self):
        registration = generics.get_object_or_404(
            Registration,
            pk=self.kwargs["pk"],
            user=self.request.user,
        )
        self.check_object_permissions(self.request, registration)
        return registration

    def post(self, request, pk):
        registration = self.get_object()

        if registration.status == Registration.Status.CANCELLED:
            return Response(
                {"detail": "Registration is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cancelled = self._cancel(registration)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            RegistrationSerializer(cancelled).data,
            status=status.HTTP_200_OK,
        )

    def _cancel(self, registration):
        with transaction.atomic():
            locked_event = (
                Event.objects.select_for_update()
                .filter(pk=registration.event_id, is_deleted=False)
                .first()
            )
            if locked_event is None:
                raise ValueError("Event not found.")

            # Re-fetch registration under the event lock
            locked_reg = (
                Registration.objects.select_for_update()
                .filter(pk=registration.pk)
                .first()
            )
            if locked_reg is None:
                raise ValueError("Registration not found.")

            if locked_reg.status == Registration.Status.CANCELLED:
                raise ValueError("Registration is already cancelled.")

            was_confirmed = locked_reg.status == Registration.Status.CONFIRMED
            locked_reg.status = Registration.Status.CANCELLED
            locked_reg.save(update_fields=["status", "updated_at"])

            if was_confirmed:
                cancel_ticket(locked_reg)

                next_waitlisted = (
                    Registration.objects.select_for_update()
                    .filter(
                        event=locked_event,
                        status=Registration.Status.WAITLISTED,
                    )
                    .order_by("created_at")
                    .first()
                )
                if next_waitlisted is not None:
                    next_waitlisted.status = Registration.Status.CONFIRMED
                    next_waitlisted.save(update_fields=["status", "updated_at"])
                    issue_ticket(next_waitlisted)


            return locked_reg

# Create your views here.
