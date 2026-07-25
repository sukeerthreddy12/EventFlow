from django.contrib import admin

from .models import Registration, TeamRegistration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "event", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "event__title"]
@admin.register(TeamRegistration)
class TeamRegistrationAdmin(admin.ModelAdmin):
    list_display = ["id", "lead", "event", "member_count", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["lead__email", "event__title"]