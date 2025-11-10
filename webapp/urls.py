from django.contrib import admin
from django.urls import path, include
from core.views import health, index

urlpatterns = [
    path("admin/", admin.site.urls),

    # health + simple hello route
    path("health", health, name="health"),
    path("hello", index, name="hello"),

    # root ("/") will be handled by the 'bench' app (dashboard)
    path("", include("bench.urls")),
]
