import math

from django.db.models import Avg, Count, FloatField, Q
from django.db.models.expressions import RawSQL
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsStationOwnerOrAdmin

from .models import Charger, Station
from .serializers import (
    ChargerSerializer,
    ChargerStatusSerializer,
    StationCreateSerializer,
    StationDetailSerializer,
    StationListSerializer,
)

HAVERSINE_SQL = (
    "6371 * ACOS(LEAST(1.0, COS(RADIANS(%s)) * COS(RADIANS(latitude)) "
    "* COS(RADIANS(longitude) - RADIANS(%s)) "
    "+ SIN(RADIANS(%s)) * SIN(RADIANS(latitude))))"
)

DEGREES_PER_KM_LAT = 1 / 111.0


def _bounding_box(lat: float, lng: float, radius_km: float):
    """Return (lat_min, lat_max, lng_min, lng_max) for a rough bounding box.
    Cheaply narrows rows before the expensive Haversine runs.
    """
    dlat = radius_km * DEGREES_PER_KM_LAT
    dlng = radius_km / (111.0 * math.cos(math.radians(lat)))
    return lat - dlat, lat + dlat, lng - dlng, lng + dlng


def _base_station_qs():
    return Station.objects.annotate(
        total_chargers=Count("chargers"),
        available_chargers=Count(
            "chargers", filter=Q(chargers__status="available")
        ),
        avg_price_kwh=Avg("chargers__base_price_per_kwh"),
    )


def _apply_geo(qs, lat, lng, radius=None):
    """Annotate queryset with Haversine distance via raw MySQL SQL.
    When radius is given, a bounding-box pre-filter is applied first so the
    expensive trigonometric Haversine only runs on the smaller candidate set.
    """
    if radius is not None:
        lat_min, lat_max, lng_min, lng_max = _bounding_box(lat, lng, radius)
        qs = qs.filter(
            latitude__gte=lat_min,
            latitude__lte=lat_max,
            longitude__gte=lng_min,
            longitude__lte=lng_max,
        )

    qs = qs.annotate(
        distance_km=RawSQL(
            HAVERSINE_SQL, (lat, lng, lat), output_field=FloatField()
        )
    )
    if radius is not None:
        qs = qs.filter(distance_km__lte=radius)
    return qs.order_by("distance_km")


class StationViewSet(viewsets.ModelViewSet):
    filterset_fields = ["city", "is_active"]
    search_fields = ["name", "address", "city"]
    ordering_fields = ["name", "city", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "nearby"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsStationOwnerOrAdmin()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return StationCreateSerializer
        if self.action == "retrieve":
            return StationDetailSerializer
        return StationListSerializer

    def get_queryset(self):
        qs = _base_station_qs()

        charger_type = self.request.query_params.get("charger_type")
        if charger_type:
            qs = qs.filter(chargers__charger_type=charger_type).distinct()

        availability = self.request.query_params.get("available")
        if availability and availability.lower() == "true":
            qs = qs.filter(available_chargers__gt=0)

        return qs

    def list(self, request, *args, **kwargs):
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius")

        if lat and lng:
            try:
                lat_f, lng_f = float(lat), float(lng)
            except (ValueError, TypeError):
                return super().list(request, *args, **kwargs)

            radius_f = None
            if radius:
                try:
                    radius_f = float(radius)
                except (ValueError, TypeError):
                    pass

            qs = _apply_geo(self.get_queryset(), lat_f, lng_f, radius_f)
            page = self.paginate_queryset(qs)
            if page is not None:
                serializer = StationListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = StationListSerializer(qs, many=True)
            return Response({"data": serializer.data})

        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"], url_path="nearby")
    def nearby(self, request):
        """Find stations within a given radius of coordinates."""
        lat = request.query_params.get("lat")
        lng = request.query_params.get("lng")
        radius = request.query_params.get("radius", "5")

        if not lat or not lng:
            return Response(
                {"error": "Both 'lat' and 'lng' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat_f, lng_f, radius_f = float(lat), float(lng), float(radius)
        except (ValueError, TypeError):
            return Response(
                {"error": "lat, lng, and radius must be valid numbers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        base_qs = _base_station_qs().filter(is_active=True)
        stations = _apply_geo(base_qs, lat_f, lng_f, radius_f)

        page = self.paginate_queryset(stations)
        if page is not None:
            serializer = StationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StationListSerializer(stations, many=True)
        return Response({"data": serializer.data})


class ChargerViewSet(viewsets.ModelViewSet):
    serializer_class = ChargerSerializer
    filterset_fields = ["charger_type", "status", "connector_type"]
    ordering_fields = ["power_kw", "base_price_per_kwh", "created_at"]
    ordering = ["-created_at"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsStationOwnerOrAdmin()]

    def get_queryset(self):
        station_id = self.kwargs.get("station_pk")
        qs = Charger.objects.select_related("station")
        if station_id:
            qs = qs.filter(station_id=station_id)
        return qs

    def perform_create(self, serializer):
        station_id = self.kwargs.get("station_pk")
        serializer.save(station_id=station_id)

    @action(detail=True, methods=["patch"], url_path="status")
    def update_status(self, request, pk=None, **kwargs):
        """Update charger status (available/busy/maintenance/offline)."""
        charger = self.get_object()
        serializer = ChargerStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        charger.status = serializer.validated_data["status"]
        charger.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "message": f"Charger status updated to '{charger.status}'.",
                "data": ChargerSerializer(charger).data,
            }
        )
