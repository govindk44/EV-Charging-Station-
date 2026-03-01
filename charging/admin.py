from django.contrib import admin

from .models import Booking, ChargingSession


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user", "charger", "status",
        "scheduled_start", "scheduled_end", "created_at",
    ]
    list_filter = ["status", "scheduled_start"]
    search_fields = ["user__email", "charger__serial_number"]
    raw_id_fields = ["user", "charger", "vehicle"]


@admin.register(ChargingSession)
class ChargingSessionAdmin(admin.ModelAdmin):
    list_display = [
        "id", "user", "charger", "status", "start_time", "end_time",
        "energy_consumed_kwh", "total_cost", "pricing_tier",
    ]
    list_filter = ["status", "pricing_tier", "start_time"]
    search_fields = ["user__email", "charger__serial_number"]
    raw_id_fields = ["user", "charger", "vehicle", "booking"]
