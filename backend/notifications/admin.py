from django.contrib import admin
from .models import EmailRetryQueue

@admin.register(EmailRetryQueue)
class EmailRetryQueueAdmin(admin.ModelAdmin):
    list_display = ("kind", "user", "event", "status", "attempts", "next_attempt_at", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("user__email", "last_error")
    readonly_fields = ("created_at", "updated_at", "last_error")