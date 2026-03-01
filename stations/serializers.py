from rest_framework import serializers

from .models import Charger, Station


class ChargerSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source="station.name", read_only=True)

    class Meta:
        model = Charger
        fields = [
            "id", "station", "station_name", "charger_type", "power_kw",
            "connector_type", "base_price_per_kwh", "status", "serial_number",
            "last_maintenance", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ChargerStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Charger.STATUS_CHOICES)


class ChargerSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Charger
        fields = [
            "id", "charger_type", "power_kw", "connector_type",
            "base_price_per_kwh", "status",
        ]


class StationListSerializer(serializers.ModelSerializer):
    total_chargers = serializers.IntegerField(read_only=True)
    available_chargers = serializers.IntegerField(read_only=True)
    avg_price_kwh = serializers.DecimalField(
        max_digits=8, decimal_places=2, read_only=True, required=False
    )
    distance_km = serializers.FloatField(read_only=True, required=False)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = Station
        fields = [
            "id", "name", "address", "city", "state", "pincode",
            "latitude", "longitude", "is_active", "opening_time",
            "closing_time", "total_chargers", "available_chargers",
            "avg_price_kwh", "distance_km", "owner_name",
            "contact_number", "amenities", "created_at",
        ]


class StationDetailSerializer(serializers.ModelSerializer):
    chargers = ChargerSummarySerializer(many=True, read_only=True)
    total_chargers = serializers.IntegerField(read_only=True)
    available_chargers = serializers.IntegerField(read_only=True)
    owner_name = serializers.CharField(source="owner.get_full_name", read_only=True)

    class Meta:
        model = Station
        fields = [
            "id", "name", "address", "city", "state", "pincode",
            "latitude", "longitude", "owner", "owner_name", "is_active",
            "opening_time", "closing_time", "amenities", "contact_number",
            "total_chargers", "available_chargers", "chargers",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = [
            "id", "name", "address", "city", "state", "pincode",
            "latitude", "longitude", "is_active", "opening_time",
            "closing_time", "amenities", "contact_number",
        ]
        read_only_fields = ["id"]

    def validate_latitude(self, value):
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90.")
        return value

    def validate_longitude(self, value):
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180.")
        return value
