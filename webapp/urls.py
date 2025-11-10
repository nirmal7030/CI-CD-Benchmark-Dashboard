from django.contrib import admin
from django.urls import path, include
from core.views import health, index

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health", health, name="health"),
    path("hello", index, name="hello"),
    path("", include("bench.urls")),
]
