from django.db import models

from accounts.models import User, Vehicle
from stations.models import Charger


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="bookings"
    )
    charger = models.ForeignKey(
        Charger, on_delete=models.CASCADE, related_name="bookings"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="bookings",
    )
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="pending"
    )
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_start", "scheduled_end"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["charger", "status", "scheduled_start", "scheduled_end"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Booking #{self.pk} - {self.user.email} on {self.charger}"


class ChargingSession(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    booking = models.OneToOneField(
        Booking, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="session",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="charging_sessions"
    )
    charger = models.ForeignKey(
        Charger, on_delete=models.CASCADE, related_name="sessions"
    )
    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="sessions",
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    energy_consumed_kwh = models.DecimalField(
        max_digits=8, decimal_places=3, default=0
    )
    base_rate_per_kwh = models.DecimalField(max_digits=6, decimal_places=2)
    peak_multiplier = models.DecimalField(
        max_digits=4, decimal_places=2, default=1.0
    )
    pricing_tier = models.CharField(max_length=20, default="normal")
    energy_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    overstay_minutes = models.PositiveIntegerField(default=0)
    overstay_fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "charging_sessions"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["user", "status"]),
            models.Index(fields=["start_time"]),
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Session #{self.pk} - {self.user.email} ({self.status})"
