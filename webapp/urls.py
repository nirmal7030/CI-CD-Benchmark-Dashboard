from django.contrib import admin
from django.http import JsonResponse
from django.urls import path

from bench import views as bench_views


def health_view(request):
    """
    Simple /health endpoint used by the GitHub Actions workflow.
    """
    return JsonResponse({"status": "ok"})


urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Health check
    path("health", health_view, name="health"),

    # Dashboard UI at /
    path("", bench_views.dashboard, name="dashboard"),

    # Metrics APIs (note the trailing slashes!)
    path("api/metrics/ingest/", bench_views.api_ingest, name="api_ingest"),
    path("api/metrics/data/", bench_views.api_metrics_data, name="api_metrics_data"),
]
