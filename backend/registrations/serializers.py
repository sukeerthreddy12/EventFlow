from rest_framework import serializers

from events.models import Event

from .models import Registration


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = [
            "id",
            "user",
            "event",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class RegistrationCreateSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()

    def validate_event_id(self, value):
        try:
            event = Event.objects.get(pk=value, is_deleted=False)
        except Event.DoesNotExist:
            raise serializers.ValidationError("Event not found.")

        if event.status != Event.Status.PUBLISHED:
            raise serializers.ValidationError(
                "Only PUBLISHED events can be registered for."
            )

        self.context["event"] = event
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        event = self.context["event"]

        if event.organiser_id == user.id:
            raise serializers.ValidationError("You cannot register for your own event.")

        already_active = Registration.objects.filter(
            user=user,
            event=event,
            status__in=[
                Registration.Status.CONFIRMED,
                Registration.Status.WAITLISTED,
            ],
        ).exists()
        if already_active:
            raise serializers.ValidationError(
                "You already have an active registration for this event."
            )
        return attrs