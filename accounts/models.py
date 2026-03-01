from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ("user", "User"),
        ("admin", "Admin"),
        ("station_owner", "Station Owner"),
    ]

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, default="")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email


class Vehicle(models.Model):
    CONNECTOR_CHOICES = [
        ("Type2", "Type 2"),
        ("CCS", "CCS"),
        ("CHAdeMO", "CHAdeMO"),
        ("GBT", "GB/T"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="vehicles")
    make = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    battery_capacity_kwh = models.DecimalField(max_digits=6, decimal_places=2)
    connector_type = models.CharField(max_length=20, choices=CONNECTOR_CHOICES)
    license_plate = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "vehicles"

    def __str__(self):
        return f"{self.make} {self.model_name} ({self.license_plate})"
