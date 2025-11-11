from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from bench import views as bench_views


def health_view(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Health check (used by your workflow)
    path("health", health_view, name="health"),

    # Dashboard UI
    path("", bench_views.dashboard, name="dashboard"),

    # Metrics APIs
    path("api/metrics/ingest/", bench_views.api_ingest, name="api_ingest"),
    path("api/metrics/data/", bench_views.api_metrics_data, name="api_metrics_data"),
]
