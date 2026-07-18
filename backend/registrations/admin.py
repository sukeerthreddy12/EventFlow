from django.contrib import admin

from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "event", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["user__email", "event__title"]