from rest_framework import serializers

from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticket
        fields = [
            "id",
            "registration",
            "token",
            "status",
            "checked_in_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class TicketCheckInSerializer(serializers.Serializer):
    token = serializers.CharField()