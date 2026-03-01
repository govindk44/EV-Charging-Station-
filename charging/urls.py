from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import BookingViewSet, ChargingSessionViewSet, PricingEstimateView

router = DefaultRouter()
router.register(r"bookings", BookingViewSet, basename="booking")
router.register(r"sessions", ChargingSessionViewSet, basename="session")

urlpatterns = [
    path("", include(router.urls)),
    path("pricing/estimate/", PricingEstimateView.as_view(), name="pricing-estimate"),
]
