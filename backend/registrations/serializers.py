from rest_framework import serializers

from events.models import Event
from django.contrib.auth import get_user_model

from .models import Registration, TeamRegistration

User = get_user_model()


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

class TeamRegistrationCreateSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    member_emails = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,  # at least 1 other member; team size >= 2
    )
    def validate_member_emails(self, emails):
        # normalize + unique
        normalized = []
        seen = set()
        for email in emails:
            email = email.lower().strip()
            if email in seen:
                raise serializers.ValidationError(f"Duplicate email: {email}")
            seen.add(email)
            normalized.append(email)
        return normalized
    def validate(self, attrs):
        request = self.context["request"]
        lead = request.user
        emails = attrs["member_emails"]
        if lead.email.lower() in emails:
            raise serializers.ValidationError(
                {"member_emails": "Do not include your own email; you are the lead."}
            )
        # reuse same event rules as individual register
        try:
            event = Event.objects.get(pk=attrs["event_id"], is_deleted=False)
        except Event.DoesNotExist:
            raise serializers.ValidationError({"event_id": "Event not found."})
        if event.status != Event.Status.PUBLISHED:
            raise serializers.ValidationError(
                {"event_id": "Only PUBLISHED events can be registered for."}
            )
        if event.is_suppressed:
            raise serializers.ValidationError(
                {"event_id": "This event is not available for registration."}
            )
        if event.organiser_id == lead.id:
            raise serializers.ValidationError(
                {"event_id": "You cannot register for your own event."}
            )
        normalized = [e.lower() for e in emails]
        members = list(User.objects.filter(email__in=normalized))
        found = {u.email.lower() for u in members}
        missing = [e for e in normalized if e not in found]
        if missing:
            raise serializers.ValidationError(
                {"member_emails": f"Users not found: {', '.join(missing)}"}
            )
        # every person (lead + members) must have no active reg on this event
        all_users = [lead, *members]
        already = Registration.objects.filter(
            user__in=all_users,
            event=event,
            status__in=[
                Registration.Status.CONFIRMED,
                Registration.Status.WAITLISTED,
            ],
        ).values_list("user__email", flat=True)
        if already:
            raise serializers.ValidationError(
                f"Already registered: {', '.join(already)}"
            )
        attrs["event"] = event
        attrs["members"] = members
        attrs["member_count"] = 1 + len(members)
        return attrs