from django.contrib import admin
from .models import Metric


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    """
    Admin configuration for viewing and filtering Metric entries.
    This will help you inspect raw data for your research.
    """

    list_display = (
        "created_at",
        "source",
        "workflow",
        "branch",
        "commit_sha",
        "lce",
        "prt",
        "smo",
        "dept",
        "clbc",
    )

    list_filter = (
        "source",
        "workflow",
        "branch",
        "created_at",
    )

    search_fields = (
        "run_id",
        "branch",
        "commit_sha",
        "notes",
    )

    readonly_fields = (
        "created_at",
    )
