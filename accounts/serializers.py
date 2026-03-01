from django.contrib.auth import authenticate
from rest_framework import serializers

from .models import User, Vehicle


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "password", "password_confirm",
            "first_name", "last_name", "phone", "role",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        if User.objects.filter(email=attrs["email"]).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["email"],
            password=attrs["password"],
        )
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    vehicles_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "phone", "role", "vehicles_count", "date_joined",
        ]
        read_only_fields = ["id", "email", "role", "date_joined"]

    def get_vehicles_count(self, obj):
        return obj.vehicles.count()


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "id", "make", "model_name", "year", "battery_capacity_kwh",
            "connector_type", "license_plate", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_year(self, value):
        if value < 2010 or value > 2030:
            raise serializers.ValidationError("Year must be between 2010 and 2030.")
        return value
