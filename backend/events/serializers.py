from rest_framework import serializers

from .models import Event


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "venue",
            "starts_at",
            "ends_at",
            "max_capacity",
            "price",
            "status",
            "refund_eligible",
            "is_featured",
            "is_suppressed",
            "organiser",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "venue",
            "starts_at",
            "ends_at",
            "max_capacity",
            "price",
        ]

    def validate_max_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than 0.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate(self, attrs):
        if attrs["ends_at"] <= attrs["starts_at"]:
            raise serializers.ValidationError(
                {"ends_at": "End time must be after start time."}
            )
        return attrs

    def create(self, validated_data):
        validated_data["organiser"] = self.context["request"].user
        validated_data["status"] = Event.Status.DRAFT
        return super().create(validated_data)


class EventUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "title",
            "description",
            "venue",
            "starts_at",
            "ends_at",
            "max_capacity",
            "price",
        ]

    def validate_max_capacity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Capacity must be greater than 0.")
        return value

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value
    

    def validate(self, attrs):
        starts_at = attrs.get("starts_at", self.instance.starts_at)
        ends_at = attrs.get("ends_at", self.instance.ends_at)
        if ends_at <= starts_at:
            raise serializers.ValidationError(
                {"ends_at": "End time must be after start time."}
            )
        return attrs

class EventAdminOverrideSerializer(serializers.Serializer):
    is_featured = serializers.BooleanField(required=False)
    is_suppressed = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Provide is_featured and/or is_suppressed."
            )
        return attrs

def soft_delete(self):
    self.is_deleted = True
    self.deleted_at = timezone.now()
    self.save(update_fields=["is_deleted", "deleted_at", "updated_at"])