import json
import statistics

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .models import Metric


def dashboard(request):
    """
    Main dashboard page.
    The HTML shell; charts fetch data from /api/metrics/data via JS.
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
        return JsonResponse(
            {"error": "Server BENCH_API_KEY not configured"}, status=500
        )

    if api_key_header != expected_key:
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # --- Parse JSON body ---
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON payload")

    # Helper: allow both short and long keys if you ever send the long ones
    def get_metric_val(short_key: str, long_key: str):
        if short_key in payload:
            return payload.get(short_key)
        if long_key in payload:
            return payload.get(long_key)
        return 0.0

    # Normalise to floats (None / "" -> 0.0)
    def as_float(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    lce_val = as_float(get_metric_val("lce", "layer_cache_efficiency"))
    prt_val = as_float(get_metric_val("prt", "pipeline_recovery_time"))
    smo_val = as_float(get_metric_val("smo", "secrets_mgmt_overhead"))
    dept_val = as_float(get_metric_val("dept", "dynamic_env_time"))
    clbc_val = as_float(get_metric_val("clbc", "cross_layer_consistency"))

    # --- Create Metric entry ---
    metric = Metric.objects.create(
        source=payload.get("source", Metric.SOURCE_GITHUB),
        workflow=payload.get("workflow", ""),
        run_id=payload.get("run_id", ""),
        run_attempt=payload.get("run_attempt", ""),
        branch=payload.get("branch", ""),
        commit_sha=payload.get("commit_sha", ""),
        lce=lce_val,
        prt=prt_val,
        smo=smo_val,
        dept=dept_val,
        clbc=clbc_val,
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
    - source: "github", "jenkins", "codepipeline" or empty/invalid for all

    Response example (shaped for dashboard.html):

    {
      "source": "github",
      "count": 10,
      "avg_lce": 75.3,
      "avg_prt": 5.1,
      "avg_smo": 1.0,
      "avg_dept": 42.0,
      "avg_clbc": 0.8,
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

    # Evaluate once, then reverse for chronological order in charts
    metrics = list(qs)
    metrics.reverse()  # oldest first

    rows = []
    lces, prts, smos, depts, clbcs = [], [], [], [], []

    for m in metrics:
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
        lces.append(m.lce)
        prts.append(m.prt)
        smos.append(m.smo)
        depts.append(m.dept)
        clbcs.append(m.clbc)

    def avg(values):
        clean = [v for v in values if v is not None]
        return float(round(statistics.fmean(clean), 2)) if clean else 0.0

    count = len(metrics)

    data = {
        "source": source,
        "count": count,
        # top-level averages for dashboard.html
        "avg_lce": avg(lces),
        "avg_prt": avg(prts),
        "avg_smo": avg(smos),
        "avg_dept": avg(depts),
        "avg_clbc": avg(clbcs),
        # keep rows for the chart
        "rows": rows,
    }

    return JsonResponse(data)
