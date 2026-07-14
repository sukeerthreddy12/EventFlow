from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "organiser",
        "status",
        "starts_at",
        "max_capacity",
        "price",
        "is_deleted",
    ]
    list_filter = ["status", "is_deleted"]
    search_fields = ["title", "venue", "organiser__email"]
    readonly_fields = ["id", "created_at", "updated_at", "deleted_at"]