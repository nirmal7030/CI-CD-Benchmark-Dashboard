import json
import statistics
from pathlib import Path

from django.conf import settings
from django.http import (
    JsonResponse,
    HttpResponse,
    HttpResponseBadRequest,
)
from django.views.decorators.csrf import csrf_exempt

from .models import Metric


def dashboard(request):
    """
    Main dashboard page – serve the static HTML directly.

    This avoids any TemplateDoesNotExist / TemplateSyntaxError problems
    while you iterate on dashboard.html.
    """
    template_path = (
        Path(settings.BASE_DIR)
        / "bench"
        / "templates"
        / "bench"
        / "dashboard.html"
    )

    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        return HttpResponse(
            f"Dashboard template not found at {template_path}",
            status=500,
            content_type="text/plain",
        )
    except Exception as exc:
        # If anything else goes wrong, show a simple error instead of a blank 500 page
        return HttpResponse(
            f"Error loading dashboard: {exc}",
            status=500,
            content_type="text/plain",
        )

    return HttpResponse(html)


@csrf_exempt
def api_ingest(request):
    """
    Ingest endpoint for CI/CD tools.
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
    """
    source = request.GET.get("source")

    qs = Metric.objects.all()

    valid_sources = {
        Metric.SOURCE_GITHUB,
        Metric.SOURCE_JENKINS,
        Metric.SOURCE_CODEPIPELINE,
    }
    if source in valid_sources:
        qs = qs.filter(source=source)
    else:
        source = "all"

    qs = qs.order_by("-created_at")[:100]
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
        # keep old top-level keys for compatibility
        "avg_lce": avg(lces),
        "avg_prt": avg(prts),
        "avg_smo": avg(smos),
        "avg_dept": avg(depts),
        "avg_clbc": avg(clbcs),
        "rows": rows,
    }

    return JsonResponse(data)
