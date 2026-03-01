from django.db import models

from accounts.models import User


class Station(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="stations"
    )
    is_active = models.BooleanField(default=True)
    opening_time = models.TimeField(default="06:00:00")
    closing_time = models.TimeField(default="23:00:00")
    amenities = models.JSONField(default=list, blank=True)
    contact_number = models.CharField(max_length=15, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "stations"
        indexes = [
            models.Index(fields=["latitude", "longitude"]),
            models.Index(fields=["latitude"]),
            models.Index(fields=["longitude"]),
            models.Index(fields=["city"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"

    def get_total_chargers(self):
        return self.chargers.count()

    def get_available_chargers(self):
        return self.chargers.filter(status="available").count()


class Charger(models.Model):
    CHARGER_TYPE_CHOICES = [
        ("Type2", "Type 2 AC"),
        ("CCS", "CCS DC"),
        ("DC-Fast", "DC Fast"),
        ("CHAdeMO", "CHAdeMO"),
    ]
    STATUS_CHOICES = [
        ("available", "Available"),
        ("busy", "Busy"),
        ("maintenance", "Maintenance"),
        ("offline", "Offline"),
    ]

    station = models.ForeignKey(
        Station, on_delete=models.CASCADE, related_name="chargers"
    )
    charger_type = models.CharField(max_length=20, choices=CHARGER_TYPE_CHOICES)
    power_kw = models.DecimalField(max_digits=6, decimal_places=2)
    connector_type = models.CharField(max_length=20)
    base_price_per_kwh = models.DecimalField(max_digits=6, decimal_places=2)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="available"
    )
    serial_number = models.CharField(max_length=50, unique=True)
    last_maintenance = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chargers"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["charger_type"]),
            models.Index(fields=["station", "status"]),
        ]

    def __str__(self):
        return f"{self.charger_type} ({self.serial_number}) - {self.station.name}"
