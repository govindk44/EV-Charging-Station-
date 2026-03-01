from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Vehicle


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["email", "username", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active"]
    search_fields = ["email", "username", "first_name", "last_name"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Extra Info", {"fields": ("phone", "role")}),
    )


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ["license_plate", "make", "model_name", "user", "connector_type"]
    list_filter = ["connector_type", "make"]
    search_fields = ["license_plate", "make", "model_name"]
