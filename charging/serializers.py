from decimal import Decimal

from rest_framework import serializers

from stations.serializers import ChargerSummarySerializer

from .models import Booking, ChargingSession


class BookingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = [
            "id", "charger", "vehicle", "scheduled_start",
            "scheduled_end", "notes",
        ]
        read_only_fields = ["id"]


class BookingListSerializer(serializers.ModelSerializer):
    charger_type = serializers.CharField(
        source="charger.charger_type", read_only=True
    )
    station_name = serializers.CharField(
        source="charger.station.name", read_only=True
    )
    charger_serial = serializers.CharField(
        source="charger.serial_number", read_only=True
    )
    vehicle_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True, default=None
    )

    class Meta:
        model = Booking
        fields = [
            "id", "charger", "charger_type", "station_name",
            "charger_serial", "vehicle", "vehicle_plate",
            "scheduled_start", "scheduled_end", "status",
            "notes", "created_at", "updated_at",
        ]


class BookingDetailSerializer(serializers.ModelSerializer):
    charger_info = ChargerSummarySerializer(source="charger", read_only=True)
    station_name = serializers.CharField(
        source="charger.station.name", read_only=True
    )
    has_session = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            "id", "user", "charger", "charger_info", "station_name",
            "vehicle", "scheduled_start", "scheduled_end", "status",
            "notes", "has_session", "created_at", "updated_at",
        ]

    def get_has_session(self, obj):
        return hasattr(obj, "session") and obj.session is not None


class SessionStartSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField(required=False)
    charger_id = serializers.IntegerField(required=False)
    vehicle_id = serializers.IntegerField(required=False)

    def validate(self, attrs):
        if not attrs.get("booking_id") and not attrs.get("charger_id"):
            raise serializers.ValidationError(
                "Either 'booking_id' or 'charger_id' is required."
            )
        return attrs


class SessionEndSerializer(serializers.Serializer):
    energy_consumed_kwh = serializers.DecimalField(
        max_digits=8, decimal_places=3, min_value=Decimal("0.001")
    )


class ChargingSessionListSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(
        source="charger.station.name", read_only=True
    )
    charger_type = serializers.CharField(
        source="charger.charger_type", read_only=True
    )
    charger_serial = serializers.CharField(
        source="charger.serial_number", read_only=True
    )
    vehicle_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True, default=None
    )
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = ChargingSession
        fields = [
            "id", "booking", "charger", "station_name", "charger_type",
            "charger_serial", "vehicle", "vehicle_plate",
            "start_time", "end_time", "duration_minutes",
            "energy_consumed_kwh", "pricing_tier", "peak_multiplier",
            "energy_cost", "overstay_minutes", "overstay_fine",
            "total_cost", "status", "created_at",
        ]

    def get_duration_minutes(self, obj):
        if obj.end_time and obj.start_time:
            return int((obj.end_time - obj.start_time).total_seconds() / 60)
        return None


class ChargingSessionDetailSerializer(serializers.ModelSerializer):
    charger_info = ChargerSummarySerializer(source="charger", read_only=True)
    station_name = serializers.CharField(
        source="charger.station.name", read_only=True
    )
    station_address = serializers.CharField(
        source="charger.station.address", read_only=True
    )
    vehicle_plate = serializers.CharField(
        source="vehicle.license_plate", read_only=True, default=None
    )
    duration_minutes = serializers.SerializerMethodField()
    invoice = serializers.SerializerMethodField()

    class Meta:
        model = ChargingSession
        fields = [
            "id", "booking", "user", "charger", "charger_info",
            "station_name", "station_address", "vehicle", "vehicle_plate",
            "start_time", "end_time", "duration_minutes",
            "energy_consumed_kwh", "base_rate_per_kwh",
            "peak_multiplier", "pricing_tier",
            "energy_cost", "overstay_minutes", "overstay_fine",
            "total_cost", "status", "invoice", "created_at", "updated_at",
        ]

    def get_duration_minutes(self, obj):
        if obj.end_time and obj.start_time:
            return int((obj.end_time - obj.start_time).total_seconds() / 60)
        return None

    def get_invoice(self, obj):
        if obj.status != "completed":
            return None
        return {
            "session_id": obj.pk,
            "energy_consumed_kwh": str(obj.energy_consumed_kwh),
            "base_rate_per_kwh": str(obj.base_rate_per_kwh),
            "pricing_tier": obj.pricing_tier,
            "peak_multiplier": str(obj.peak_multiplier),
            "energy_cost": str(obj.energy_cost),
            "overstay_minutes": obj.overstay_minutes,
            "overstay_fine_per_minute": "5.00",
            "overstay_fine": str(obj.overstay_fine),
            "total_cost": str(obj.total_cost),
            "currency": "INR",
        }


class PricingEstimateSerializer(serializers.Serializer):
    charger_id = serializers.IntegerField()
    duration_hours = serializers.FloatField(min_value=0.1, max_value=24.0)
    start_hour = serializers.IntegerField(
        min_value=0, max_value=23, required=False
    )


class CostPreviewSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()
