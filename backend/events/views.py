from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView



from notifications.tasks import send_event_cancelled_task
from registrations.models import Registration
from django.db import transaction
from django.utils import timezone


from accounts.permissions import IsOrganiser

from .models import Event
from .permissions import IsEventOrganiser
from accounts.permissions import IsAdmin
from .serializers import (
    EventCreateSerializer,
    EventSerializer,
    EventUpdateSerializer,
    EventAdminOverrideSerializer,
    PublicEventSerializer,
)

@extend_schema_view(
    get=extend_schema(tags=["Events"], summary="List published events (public)"),
)
class PublicEventListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicEventSerializer
    def get_queryset(self):
        return Event.objects.filter(
            status=Event.Status.PUBLISHED,
            is_deleted=False,
            is_suppressed=False,
        )

@extend_schema_view(
    get=extend_schema(tags=["Events"], summary="Published event detail (public)"),
)
class PublicEventDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    serializer_class = PublicEventSerializer

    def get_queryset(self):
        return Event.objects.filter(
            status=Event.Status.PUBLISHED,
            is_deleted=False,
            is_suppressed=False,
        )



@extend_schema_view(
    get=extend_schema(tags=["Events"], summary="List my events"),
    post=extend_schema(tags=["Events"], summary="Create event"),
)
class EventListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsOrganiser]

    def get_queryset(self):
        return Event.objects.filter(
            organiser=self.request.user,
            is_deleted=False,
        )

    def get_serializer_class(self):
        if self.request.method == "POST":
            return EventCreateSerializer
        return EventSerializer


@extend_schema_view(
    get=extend_schema(tags=["Events"], summary="Get event detail"),
    patch=extend_schema(tags=["Events"], summary="Update event"),
    delete=extend_schema(tags=["Events"], summary=" soft delete event"),
)
class EventDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOrganiser, IsEventOrganiser]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        return Event.objects.filter(
            organiser=self.request.user,
            is_deleted=False,
        )

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return EventUpdateSerializer
        return EventSerializer
    def destroy(self, request, *args, **kwargs):
        event = self.get_object()  # already checks ownership + not deleted
        event.soft_delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    post=extend_schema(tags=["Events"], summary="Publish event"),
)
class EventPublishView(APIView):
    permission_classes = [IsAuthenticated, IsOrganiser, IsEventOrganiser]
    def get_object(self):
        event = generics.get_object_or_404(
            Event,
            pk=self.kwargs["pk"],
            organiser=self.request.user,
            is_deleted=False,
        )
        self.check_object_permissions(self.request, event)
        return event
    def post(self, request, pk):
        event = self.get_object()
        if event.status != Event.Status.DRAFT:
            return Response(
                {"detail": "Only DRAFT events can be published."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        now = timezone.now()
        if event.ends_at <= now:
            return Response(
                {"detail": "Cannot publish an event that has already ended."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if event.starts_at <= now:
            return Response(
                {"detail": "Cannot publish an event that has already started. Update the schedule first."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = Event.Status.PUBLISHED
        event.save(update_fields=["status", "updated_at"])
        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)



@extend_schema_view(
    post=extend_schema(tags=["Events"], summary="Unpublish event"),
)
class EventUnpublishView(APIView):
    permission_classes = [IsAuthenticated, IsOrganiser, IsEventOrganiser]
    def get_object(self):
        event = generics.get_object_or_404(
            Event,
            pk=self.kwargs["pk"],
            organiser=self.request.user,
            is_deleted=False,
        )
        self.check_object_permissions(self.request, event)
        return event
    def post(self, request, pk):
        event = self.get_object()
        if event.status != Event.Status.PUBLISHED:
            return Response(
                {"detail": "Only PUBLISHED events can be unpublished."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        event.status = Event.Status.DRAFT
        event.save(update_fields=["status", "updated_at"])
        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)

@extend_schema_view(
    post=extend_schema(tags=["Events"], summary="Cancel event"),
)
class EventCancelView(APIView):
    permission_classes = [IsAuthenticated, IsOrganiser, IsEventOrganiser]

    def get_object(self):
        event = generics.get_object_or_404(
            Event,
            pk=self.kwargs["pk"],
            organiser=self.request.user,
            is_deleted=False,
        )
        self.check_object_permissions(self.request, event)
        return event

    def post(self, request, pk):
        event = self.get_object()

        if event.status == Event.Status.CANCELLED:
            return Response(
                {"detail": "Event is already cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if event.status == Event.Status.COMPLETED:
            return Response(
                {"detail": "Completed events cannot be cancelled."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Allow cancel from DRAFT / PUBLISHED / ONGOING
        event.status = Event.Status.CANCELLED
        event.refund_eligible = True
        event.save(update_fields=["status", "refund_eligible", "updated_at"])

        registrant_ids = list(
            Registration.objects.filter(
                event=event,
                status__in=[
                    Registration.Status.CONFIRMED,
                    Registration.Status.WAITLISTED,
                ],
            ).values_list("user_id", flat=True)
        )
        event_id = str(event.id)
        for user_id in registrant_ids:
            uid = str(user_id)
            transaction.on_commit(
                lambda uid=uid: send_event_cancelled_task.delay(uid, event_id)
            )

        # TODO: bulk notify all registrants (Celery) — Phase notifications

        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)
@extend_schema_view(
    patch=extend_schema(
        tags=["Events"],
        summary="Admin override (feature/suppress)",
        request=EventAdminOverrideSerializer,
    ),
)
class EventAdminOverrideView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    def patch(self, request, pk):
        event = generics.get_object_or_404(Event, pk=pk, is_deleted=False)
        serializer = EventAdminOverrideSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(event, field, value)
        event.save(
            update_fields=[*serializer.validated_data.keys(), "updated_at"]
        )
        return Response(EventSerializer(event).data, status=status.HTTP_200_OK)
