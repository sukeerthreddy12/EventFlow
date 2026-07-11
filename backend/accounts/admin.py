from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_verified", "is_active", "is_staff"]
    list_filter = ["role", "is_verified", "is_active", "is_staff"]
    search_fields = ["username", "email"]
    ordering = ["username"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Account info", {"fields": ("role", "is_verified")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Account info", {"fields": ("role", "is_verified")}),
    )
