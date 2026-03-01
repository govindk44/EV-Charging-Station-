from django.contrib import admin

from .models import Charger, Station


class ChargerInline(admin.TabularInline):
    model = Charger
    extra = 0
    fields = [
        "charger_type", "power_kw", "connector_type",
        "base_price_per_kwh", "status", "serial_number",
    ]


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = [
        "name", "city", "is_active", "latitude", "longitude", "owner",
    ]
    list_filter = ["city", "is_active", "state"]
    search_fields = ["name", "address", "city"]
    inlines = [ChargerInline]


@admin.register(Charger)
class ChargerAdmin(admin.ModelAdmin):
    list_display = [
        "serial_number", "station", "charger_type", "power_kw",
        "base_price_per_kwh", "status",
    ]
    list_filter = ["charger_type", "status"]
    search_fields = ["serial_number", "station__name"]
