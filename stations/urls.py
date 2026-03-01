from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ChargerViewSet, StationViewSet

router = DefaultRouter()
router.register(r"", StationViewSet, basename="station")

charger_router = DefaultRouter()
charger_router.register(r"chargers", ChargerViewSet, basename="charger")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:station_pk>/",
        include(charger_router.urls),
    ),
]
