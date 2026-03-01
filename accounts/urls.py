from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import LoginView, LogoutView, ProfileView, RegisterView, VehicleViewSet

router = DefaultRouter()
router.register(r"vehicles", VehicleViewSet, basename="vehicle")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("", include(router.urls)),
]
