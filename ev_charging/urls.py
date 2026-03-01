from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/stations/", include("stations.urls")),
    path("api/", include("charging.urls")),
]
