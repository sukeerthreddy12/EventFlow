from django.contrib import admin

from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ["id", "registration", "status", "token", "checked_in_at", "created_at"]
    list_filter = ["status"]
    search_fields = ["token", "registration__user__email"]
    readonly_fields = ["id", "token", "created_at", "updated_at", "checked_in_at"]