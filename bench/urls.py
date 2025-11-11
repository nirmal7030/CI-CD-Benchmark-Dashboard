from django.urls import path
from . import views

urlpatterns = [
    # Dashboard (HTML)
    path("", views.dashboard, name="dashboard"),

    # API endpoints (with trailing slashes to match JS fetch & CI calls)
    path("api/metrics/ingest/", views.api_ingest, name="api_ingest"),
    path("api/metrics/data/", views.api_metrics_data, name="api_metrics_data"),
]
