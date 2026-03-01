from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """Object-level: allow write only when request.user owns the object.

    Ownership is resolved via ``obj.user`` (bookings, sessions, vehicles).
    Safe methods (GET, HEAD, OPTIONS) are always allowed.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "user", None) == request.user


class IsStationOwnerOrAdmin(BasePermission):
    """View + object level: restricts mutating station/charger data to
    station owners (their own stations) and admins (any station)."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role in ("admin", "station_owner")

    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        owner = getattr(obj, "owner", None) or getattr(obj, "station", None)
        if hasattr(owner, "owner"):
            owner = owner.owner
        return owner == request.user


class IsAdminUser(BasePermission):
    """Allow access only to admin users."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "admin"
        )
