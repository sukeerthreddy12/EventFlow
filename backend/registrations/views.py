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


from notifications.tasks import (
    send_registration_confirmed_task,
    send_waitlist_joined_task,
    send_waitlist_promoted_task,
)

from .models import Registration,TeamRegistration
from .serializers import RegistrationCreateSerializer, RegistrationSerializer, TeamRegistrationCreateSerializer


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

            if locked_event.is_suppressed:
                raise ValueError("This event is not available for registration.")
            

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
                user_id = str(user.id)
                event_id = str(locked_event.id)
                transaction.on_commit(
                     lambda: send_registration_confirmed_task.delay(user_id, event_id)
                 )
            else:
                user_id = str(user.id)
                event_id = str(locked_event.id)
                transaction.on_commit(
                    lambda: send_waitlist_joined_task.delay(user_id, event_id)
                )


            return registration

@extend_schema(tags=["Registrations"], summary="Cancel my registration")
class RegistrationCancelView(APIView):
    permission_classes = [IsAuthenticated, IsRegistrationOwner]

    def _next_waitlisted_party(self, locked_event):
        """Returns ("solo", reg, 1) or ("team", team, member_count) or None."""
        next_solo = (
            Registration.objects.select_for_update()
            .filter(
                event=locked_event,
                status=Registration.Status.WAITLISTED,
                team__isnull=True,
            )
            .order_by("created_at")
            .first()
        )
        next_team = (
            TeamRegistration.objects.select_for_update()
            .filter(
                event=locked_event,
                status=TeamRegistration.Status.WAITLISTED,
            )
            .order_by("created_at")
            .first()
        )

        if next_solo is None and next_team is None:
            return None
        if next_team is None:
            return ("solo", next_solo, 1)
        if next_solo is None:
            return ("team", next_team, next_team.member_count)
        if next_solo.created_at <= next_team.created_at:
            return ("solo", next_solo, 1)
        return ("team", next_team, next_team.member_count)

    def _promote_waitlist(self, locked_event, free_seats: int):
        while free_seats > 0:
            party = self._next_waitlisted_party(locked_event)
            if party is None:
                break

            kind, obj, size = party
            if size > free_seats:
                break  # do not skip ahead

            if kind == "solo":
                obj.status = Registration.Status.CONFIRMED
                obj.save(update_fields=["status", "updated_at"])
                issue_ticket(obj)
                uid = str(obj.user_id)
                eid = str(locked_event.id)
                transaction.on_commit(
                    lambda: send_waitlist_promoted_task.delay(uid, eid)
                )
            else:
                obj.status = TeamRegistration.Status.CONFIRMED
                obj.save(update_fields=["status", "updated_at"])
                for reg in obj.registrations.select_for_update().filter(
                    status=Registration.Status.WAITLISTED
                ):
                    reg.status = Registration.Status.CONFIRMED
                    reg.save(update_fields=["status", "updated_at"])
                    issue_ticket(reg)
                    uid = str(reg.user_id)
                    eid = str(locked_event.id)
                    transaction.on_commit(
                    lambda uid=uid, eid=eid: send_waitlist_promoted_task.delay(uid, eid)
                    )

            free_seats -= size

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

            locked_reg = (
                Registration.objects.select_for_update()
                .filter(pk=registration.pk)
                .first()
            )
            if locked_reg is None:
                raise ValueError("Registration not found.")
            if locked_reg.status == Registration.Status.CANCELLED:
                raise ValueError("Registration is already cancelled.")

            free_seats = 0

            if locked_reg.team_id:
                team = (
                    TeamRegistration.objects.select_for_update()
                    .filter(pk=locked_reg.team_id)
                    .first()
                )
                if team is None:
                    raise ValueError("Team not found.")
                if team.status == TeamRegistration.Status.CANCELLED:
                    raise ValueError("Team is already cancelled.")

                members = list(
                    team.registrations.select_for_update().filter(
                        status__in=[
                            Registration.Status.CONFIRMED,
                            Registration.Status.WAITLISTED,
                        ]
                    )
                )
                for reg in members:
                    was_confirmed = reg.status == Registration.Status.CONFIRMED
                    reg.status = Registration.Status.CANCELLED
                    reg.save(update_fields=["status", "updated_at"])
                    if was_confirmed:
                        cancel_ticket(reg)
                        free_seats += 1

                team.status = TeamRegistration.Status.CANCELLED
                team.save(update_fields=["status", "updated_at"])
                locked_reg.refresh_from_db()
            else:
                was_confirmed = locked_reg.status == Registration.Status.CONFIRMED
                locked_reg.status = Registration.Status.CANCELLED
                locked_reg.save(update_fields=["status", "updated_at"])
                if was_confirmed:
                    cancel_ticket(locked_reg)
                    free_seats = 1

            if free_seats > 0:
                self._promote_waitlist(locked_event, free_seats)

            return locked_reg

@extend_schema(
    tags=["Registrations"],
    summary="Register a team for an event",
    request=TeamRegistrationCreateSerializer,
)
class TeamRegistrationCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAttendeeOrOrganiser]
    def post(self, request):
        serializer = TeamRegistrationCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            team, registrations = self._register_team(
                lead=request.user,
                event=serializer.validated_data["event"],
                members=serializer.validated_data["members"],
                member_count=serializer.validated_data["member_count"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                "id": str(team.id),
                "group_token": team.group_token,
                "event": str(team.event_id),
                "lead": str(team.lead_id),
                "member_count": team.member_count,
                "status": team.status,
                "registrations": RegistrationSerializer(registrations, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )
    def _register_team(self, lead, event, members, member_count):
        with transaction.atomic():
            locked_event = (
                Event.objects.select_for_update()
                .filter(pk=event.pk, is_deleted=False)
                .first()
            )
            if locked_event is None:
                raise ValueError("Event not found.")
            if locked_event.status != Event.Status.PUBLISHED:
                raise ValueError("Only PUBLISHED events can be registered for.")
            if locked_event.organiser_id == lead.id:
                raise ValueError("You cannot register for your own event.")
            if locked_event.is_suppressed:
                raise ValueError("This event is not available for registration.")
            all_users = [lead, *members]
            if Registration.objects.filter(
                user__in=all_users,
                event=locked_event,
                status__in=[
                    Registration.Status.CONFIRMED,
                    Registration.Status.WAITLISTED,
                ],
            ).exists():
                raise ValueError(
                    "One or more members already have an active registration."
                )
            confirmed_count = Registration.objects.filter(
                event=locked_event,
                status=Registration.Status.CONFIRMED,
            ).count()
            free = locked_event.max_capacity - confirmed_count
            status_value = (
                Registration.Status.CONFIRMED
                if free >= member_count
                else Registration.Status.WAITLISTED
            )
            team = TeamRegistration.objects.create(
                lead=lead,
                event=locked_event,
                member_count=member_count,
                status=status_value,
            )
            registrations = []
            for user in all_users:
                reg = Registration.objects.create(
                    user=user,
                    event=locked_event,
                    team=team,
                    status=status_value,
                )
                if status_value == Registration.Status.CONFIRMED:
                    issue_ticket(reg)
                registrations.append(reg)

            event_id = str(locked_event.id)
            if status_value == Registration.Status.CONFIRMED:
                for reg in registrations:
                    uid = str(reg.user_id)
                    transaction.on_commit(
                        lambda uid=uid: send_registration_confirmed_task.delay(
                            uid, event_id
                        )
                    )
            else:
                for reg in registrations:
                    uid = str(reg.user_id)
                    transaction.on_commit(
                        lambda uid=uid: send_waitlist_joined_task.delay(uid, event_id)
                    )

            return team, registrations

            
# Create your views here.
