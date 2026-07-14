from rest_framework.permissions import BasePermission


class IsEventOrganiser(BasePermission):
    """Object-level: only the event's organiser (or later admin)."""

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_authenticated
            and obj.organiser_id == request.user.id
        )

