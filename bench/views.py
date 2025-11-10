import json
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Metric


def dashboard(request):
    """
    Main dashboard page.
    Later we'll add charts and client-side JS that call /api/metrics/data.
    """
    return render(request, "bench/dashboard.html")


@csrf_exempt
def api_ingest(request):
    """
    Ingest endpoint for CI/CD tools.

    Expected:
    - Method: POST
    - Header: X-Bench-Key: <BENCH_API_KEY>
    - Body (JSON), e.g.:

      {
        "source": "github",
        "workflow": "CI",
        "run_id": "12345",
        "run_attempt": "1",
        "branch": "main",
        "commit_sha": "abc123",

        "lce": 80.5,
        "prt": 0.0,
        "smo": 1.2,
        "dept": 45.0,
        "clbc": 1.0,
        "notes": "clean build"
      }
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # --- API key check ---
    api_key_header = request.headers.get("X-Bench-Key")
    expected_key = getattr(settings, "BENCH_API_KEY", None)

    if not expected_key:
        return JsonResponse({"error": "Server BENCH_API_KEY not configured"}, status=500)

    if api_key_header != expected_key:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # --- Parse JSON body ---
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON payload")

    # --- Create Metric entry ---
    metric = Metric.objects.create(
        source=payload.get("source", Metric.SOURCE_GITHUB),
        workflow=payload.get("workflow", ""),
        run_id=payload.get("run_id", ""),
        run_attempt=payload.get("run_attempt", ""),
        branch=payload.get("branch", ""),
        commit_sha=payload.get("commit_sha", ""),
        lce=float(payload.get("lce") or 0.0),
        prt=float(payload.get("prt") or 0.0),
        smo=float(payload.get("smo") or 0.0),
        dept=float(payload.get("dept") or 0.0),
        clbc=float(payload.get("clbc") or 0.0),
        notes=payload.get("notes", ""),
    )

    return JsonResponse(
        {
            "status": "stored",
            "id": metric.id,
            "created_at": metric.created_at.isoformat(),
        }
    )


def api_metrics_data(request):
    """
    Returns recent metrics and aggregates for a given source.

    Query params:
    - source: "github", "jenkins", "codepipeline" or empty for all

    Response example:

    {
      "source": "github",
      "count": 10,
      "avg": {
        "lce": 75.3,
        "prt": 5.1,
        "smo": 1.0,
        "dept": 42.0,
        "clbc": 0.8
      },
      "rows": [
        {
          "t": "2025-11-10T12:34:56",
          "lce": 80.0,
          "prt": 0.0,
          "smo": 1.2,
          "dept": 40.0,
          "clbc": 1.0
        },
        ...
      ]
    }
    """
    source = request.GET.get("source")

    qs = Metric.objects.all()

    # Filter by source if provided and valid
    valid_sources = {
        Metric.SOURCE_GITHUB,
        Metric.SOURCE_JENKINS,
        Metric.SOURCE_CODEPIPELINE,
    }
    if source in valid_sources:
        qs = qs.filter(source=source)
    else:
        # if source is invalid or empty, we treat it as "all sources"
        source = "all"

    # Limit to last 100 entries (newest first)
    qs = qs.order_by("-created_at")[:100]

    # Build list of rows (reverse to chronological order)
    rows = []
    total_lce = total_prt = total_smo = total_dept = total_clbc = 0.0

    for m in reversed(qs):  # oldest first
        rows.append(
            {
                "t": m.created_at.isoformat(),
                "lce": m.lce,
                "prt": m.prt,
                "smo": m.smo,
                "dept": m.dept,
                "clbc": m.clbc,
            }
        )
        total_lce += m.lce
        total_prt += m.prt
        total_smo += m.smo
        total_dept += m.dept
        total_clbc += m.clbc

    count = qs.count() if hasattr(qs, "count") else len(rows)
    if count > 0:
        avg_lce = total_lce / count
        avg_prt = total_prt / count
        avg_smo = total_smo / count
        avg_dept = total_dept / count
        avg_clbc = total_clbc / count
    else:
        avg_lce = avg_prt = avg_smo = avg_dept = avg_clbc = 0.0

    data = {
        "source": source,
        "count": count,
        "avg": {
            "lce": avg_lce,
            "prt": avg_prt,
            "smo": avg_smo,
            "dept": avg_dept,
            "clbc": avg_clbc,
        },
        "rows": rows,
    }

    return JsonResponse(data)
