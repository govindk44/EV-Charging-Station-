from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import IsOwnerOrReadOnly
from stations.models import Charger

from .models import Booking, ChargingSession
from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
    ChargingSessionDetailSerializer,
    ChargingSessionListSerializer,
    PricingEstimateSerializer,
    SessionEndSerializer,
    SessionStartSerializer,
)
from .services import BookingService, PricingService, SessionService


class BookingViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ["get", "post", "patch", "head", "options"]
    filterset_fields = ["status"]
    ordering_fields = ["scheduled_start", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return BookingCreateSerializer
        if self.action == "retrieve":
            return BookingDetailSerializer
        return BookingListSerializer

    def get_queryset(self):
        qs = Booking.objects.filter(user=self.request.user).select_related(
            "charger", "charger__station", "vehicle"
        )

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(scheduled_start__date__gte=date_from)
        if date_to:
            qs = qs.filter(scheduled_end__date__lte=date_to)

        return qs

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = BookingService.create_booking(
            user=request.user,
            charger_id=serializer.validated_data["charger"].pk,
            vehicle_id=(
                serializer.validated_data["vehicle"].pk
                if serializer.validated_data.get("vehicle")
                else None
            ),
            scheduled_start=serializer.validated_data["scheduled_start"],
            scheduled_end=serializer.validated_data["scheduled_end"],
            notes=serializer.validated_data.get("notes", ""),
        )

        start_hour = booking.scheduled_start.hour
        estimate = PricingService.estimate_cost(
            booking.charger,
            duration_hours=(
                (booking.scheduled_end - booking.scheduled_start).total_seconds()
                / 3600
            ),
            start_hour=start_hour,
        )

        return Response(
            {
                "message": "Booking confirmed successfully.",
                "data": BookingDetailSerializer(booking).data,
                "pricing_estimate": estimate,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["patch"], url_path="cancel")
    def cancel(self, request, pk=None):
        booking = self.get_object()
        if booking.status in ("completed", "cancelled"):
            return Response(
                {"error": f"Cannot cancel a {booking.status} booking."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking.status = "cancelled"
        booking.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "message": "Booking cancelled successfully.",
                "data": BookingListSerializer(booking).data,
            }
        )


class ChargingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    filterset_fields = ["status"]
    ordering_fields = ["start_time", "total_cost", "created_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ChargingSessionDetailSerializer
        return ChargingSessionListSerializer

    def get_queryset(self):
        qs = ChargingSession.objects.filter(
            user=self.request.user
        ).select_related("charger", "charger__station", "vehicle", "booking")

        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from:
            qs = qs.filter(start_time__date__gte=date_from)
        if date_to:
            qs = qs.filter(start_time__date__lte=date_to)

        return qs

    @action(detail=False, methods=["post"], url_path="start")
    def start_session(self, request):
        serializer = SessionStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = SessionService.start_session(
            user=request.user,
            booking_id=serializer.validated_data.get("booking_id"),
            charger_id=serializer.validated_data.get("charger_id"),
            vehicle_id=serializer.validated_data.get("vehicle_id"),
        )

        return Response(
            {
                "message": "Charging session started.",
                "data": ChargingSessionDetailSerializer(session).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="end")
    def end_session(self, request, pk=None):
        serializer = SessionEndSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = SessionService.end_session(
            session_id=pk,
            user=request.user,
            energy_consumed_kwh=serializer.validated_data["energy_consumed_kwh"],
        )

        return Response(
            {
                "message": "Charging session completed.",
                "data": ChargingSessionDetailSerializer(session).data,
            }
        )

    @action(detail=True, methods=["get"], url_path="cost-preview")
    def cost_preview(self, request, pk=None):
        """Preview current cost of an active session."""
        try:
            session = ChargingSession.objects.select_related(
                "charger", "booking"
            ).get(pk=pk, user=request.user)
        except ChargingSession.DoesNotExist:
            return Response(
                {"error": "Session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if session.status == "completed":
            return Response(
                {
                    "message": "Session already completed.",
                    "data": ChargingSessionDetailSerializer(session).data,
                }
            )

        now = timezone.now()
        duration_hours = (now - session.start_time).total_seconds() / 3600
        estimated_kwh = session.charger.power_kw * round(duration_hours, 2)

        pricing = PricingService.calculate_effective_rate(
            session.base_rate_per_kwh,
            session.start_time.hour,
            session.charger.charger_type,
        )

        estimated_cost = float(estimated_kwh * pricing["effective_rate"])

        overstay_minutes = 0
        overstay_fine = 0.0
        if session.booking and now > session.booking.scheduled_end:
            overstay_minutes = int(
                (now - session.booking.scheduled_end).total_seconds() / 60
            )
            overstay_fine = overstay_minutes * 5.0

        return Response(
            {
                "data": {
                    "session_id": session.pk,
                    "duration_hours": round(duration_hours, 2),
                    "estimated_kwh": float(round(estimated_kwh, 2)),
                    "effective_rate_per_kwh": str(pricing["effective_rate"]),
                    "peak_multiplier": str(pricing["multiplier"]),
                    "pricing_tier": pricing["tier"],
                    "estimated_cost": round(estimated_cost, 2),
                    "overstay_minutes": overstay_minutes,
                    "overstay_fine": round(overstay_fine, 2),
                    "estimated_total": round(
                        estimated_cost + overstay_fine, 2
                    ),
                    "currency": "INR",
                }
            }
        )


class PricingEstimateView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        serializer = PricingEstimateSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        charger_id = serializer.validated_data["charger_id"]
        duration_hours = serializer.validated_data["duration_hours"]
        start_hour = serializer.validated_data.get(
            "start_hour", timezone.now().hour
        )

        try:
            charger = Charger.objects.get(pk=charger_id)
        except Charger.DoesNotExist:
            return Response(
                {"error": "Charger not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        estimate = PricingService.estimate_cost(
            charger, duration_hours, start_hour
        )
        return Response({"data": estimate})
