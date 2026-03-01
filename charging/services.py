from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from core.utils import (
    DC_FAST_SURCHARGE_PER_KWH,
    OVERSTAY_FINE_PER_MINUTE,
    get_pricing_label,
    get_pricing_multiplier,
)
from stations.models import Charger

from .models import Booking, ChargingSession


class PricingService:
    """Handles all dynamic pricing calculations."""

    @staticmethod
    def calculate_effective_rate(
        base_price: Decimal, hour: int, charger_type: str
    ) -> dict:
        multiplier = get_pricing_multiplier(hour)
        tier = get_pricing_label(hour)
        effective_rate = base_price * multiplier

        if charger_type == "DC-Fast":
            effective_rate += DC_FAST_SURCHARGE_PER_KWH

        return {
            "base_rate": base_price,
            "multiplier": multiplier,
            "tier": tier,
            "effective_rate": effective_rate.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "surcharge": (
                DC_FAST_SURCHARGE_PER_KWH
                if charger_type == "DC-Fast"
                else Decimal("0.00")
            ),
        }

    @staticmethod
    def estimate_cost(
        charger: Charger, duration_hours: float, start_hour: int
    ) -> dict:
        pricing = PricingService.calculate_effective_rate(
            charger.base_price_per_kwh, start_hour, charger.charger_type
        )
        estimated_kwh = Decimal(str(duration_hours)) * charger.power_kw
        estimated_cost = (estimated_kwh * pricing["effective_rate"]).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        return {
            "charger_type": charger.charger_type,
            "power_kw": charger.power_kw,
            "base_rate_per_kwh": pricing["base_rate"],
            "peak_multiplier": pricing["multiplier"],
            "pricing_tier": pricing["tier"],
            "effective_rate_per_kwh": pricing["effective_rate"],
            "estimated_kwh": estimated_kwh.quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            ),
            "estimated_cost": estimated_cost,
            "duration_hours": duration_hours,
            "overstay_fine": Decimal("0.00"),
            "currency": "INR",
        }

    @staticmethod
    def calculate_session_cost(session: ChargingSession) -> dict:
        """Calculate final cost for a completed session."""
        pricing = PricingService.calculate_effective_rate(
            session.base_rate_per_kwh,
            session.start_time.hour,
            session.charger.charger_type,
        )

        energy_cost = (
            session.energy_consumed_kwh * pricing["effective_rate"]
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        overstay_minutes = 0
        overstay_fine = Decimal("0.00")

        if session.booking and session.end_time:
            scheduled_end = session.booking.scheduled_end
            if session.end_time > scheduled_end:
                delta = session.end_time - scheduled_end
                overstay_minutes = int(delta.total_seconds() / 60)
                overstay_fine = (
                    Decimal(str(overstay_minutes)) * OVERSTAY_FINE_PER_MINUTE
                )

        total_cost = energy_cost + overstay_fine

        return {
            "energy_cost": energy_cost,
            "overstay_minutes": overstay_minutes,
            "overstay_fine": overstay_fine,
            "total_cost": total_cost,
            "peak_multiplier": pricing["multiplier"],
            "pricing_tier": pricing["tier"],
            "effective_rate": pricing["effective_rate"],
        }


class BookingService:
    """Handles booking creation with concurrency-safe double-booking prevention."""

    @staticmethod
    def create_booking(
        user, charger_id: int, vehicle_id: int | None,
        scheduled_start: datetime, scheduled_end: datetime, notes: str = "",
    ) -> Booking:
        if scheduled_start >= scheduled_end:
            raise ValidationError(
                {"scheduled_end": "End time must be after start time."}
            )

        if scheduled_start < timezone.now():
            raise ValidationError(
                {"scheduled_start": "Cannot book in the past."}
            )

        max_duration_hours = 8
        duration = (scheduled_end - scheduled_start).total_seconds() / 3600
        if duration > max_duration_hours:
            raise ValidationError(
                {"scheduled_end": f"Maximum booking duration is {max_duration_hours} hours."}
            )

        with transaction.atomic():
            try:
                charger = Charger.objects.select_for_update().get(pk=charger_id)
            except Charger.DoesNotExist:
                raise ValidationError({"charger": "Charger not found."})

            if charger.status in ("maintenance", "offline"):
                raise ValidationError(
                    {"charger": f"Charger is currently {charger.status}."}
                )

            overlapping = Booking.objects.filter(
                charger=charger,
                status__in=["pending", "confirmed", "active"],
                scheduled_start__lt=scheduled_end,
                scheduled_end__gt=scheduled_start,
            ).exists()

            if overlapping:
                raise ValidationError(
                    {"charger": "This charger is already booked for the requested time slot."}
                )

            booking = Booking.objects.create(
                user=user,
                charger=charger,
                vehicle_id=vehicle_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                status="confirmed",
                notes=notes,
            )

        return booking


class SessionService:
    """Handles charging session lifecycle: start → end → invoice."""

    @staticmethod
    def start_session(
        user, booking_id: int | None = None, charger_id: int | None = None,
        vehicle_id: int | None = None,
    ) -> ChargingSession:
        now = timezone.now()

        with transaction.atomic():
            if booking_id:
                try:
                    booking = Booking.objects.select_for_update().get(
                        pk=booking_id, user=user
                    )
                except Booking.DoesNotExist:
                    raise ValidationError({"booking": "Booking not found."})

                if booking.status not in ("confirmed", "pending"):
                    raise ValidationError(
                        {"booking": f"Cannot start session for a {booking.status} booking."}
                    )

                charger = Charger.objects.select_for_update().get(
                    pk=booking.charger_id
                )
                vehicle_id = vehicle_id or (
                    booking.vehicle_id if booking.vehicle else None
                )

                booking.status = "active"
                booking.save(update_fields=["status", "updated_at"])

            elif charger_id:
                try:
                    charger = Charger.objects.select_for_update().get(pk=charger_id)
                except Charger.DoesNotExist:
                    raise ValidationError({"charger": "Charger not found."})
                booking = None
            else:
                raise ValidationError(
                    {"detail": "Either booking_id or charger_id is required."}
                )

            if charger.status != "available":
                raise ValidationError(
                    {"charger": f"Charger is currently {charger.status}."}
                )

            active_sessions = ChargingSession.objects.filter(
                charger=charger, status="active"
            ).exists()
            if active_sessions:
                raise ValidationError(
                    {"charger": "Charger already has an active session."}
                )

            pricing = PricingService.calculate_effective_rate(
                charger.base_price_per_kwh, now.hour, charger.charger_type
            )

            session = ChargingSession.objects.create(
                booking=booking,
                user=user,
                charger=charger,
                vehicle_id=vehicle_id,
                start_time=now,
                base_rate_per_kwh=charger.base_price_per_kwh,
                peak_multiplier=pricing["multiplier"],
                pricing_tier=pricing["tier"],
                status="active",
            )

            charger.status = "busy"
            charger.save(update_fields=["status", "updated_at"])

        return session

    @staticmethod
    def end_session(
        session_id: int, user, energy_consumed_kwh: Decimal
    ) -> ChargingSession:
        now = timezone.now()

        with transaction.atomic():
            try:
                session = ChargingSession.objects.select_for_update().get(
                    pk=session_id, user=user
                )
            except ChargingSession.DoesNotExist:
                raise ValidationError({"session": "Session not found."})

            if session.status != "active":
                raise ValidationError(
                    {"session": f"Session is already {session.status}."}
                )

            session.end_time = now
            session.energy_consumed_kwh = energy_consumed_kwh

            cost_data = PricingService.calculate_session_cost(session)

            session.energy_cost = cost_data["energy_cost"]
            session.overstay_minutes = cost_data["overstay_minutes"]
            session.overstay_fine = cost_data["overstay_fine"]
            session.total_cost = cost_data["total_cost"]
            session.status = "completed"
            session.save()

            charger = Charger.objects.select_for_update().get(
                pk=session.charger_id
            )
            charger.status = "available"
            charger.save(update_fields=["status", "updated_at"])

            if session.booking:
                session.booking.status = "completed"
                session.booking.save(update_fields=["status", "updated_at"])

        session.refresh_from_db()
        return session
