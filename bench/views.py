import json
import statistics
import logging
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Metric

logger = logging.getLogger(__name__)

def dashboard(request):
    """Render main dashboard shell (JS fetches data dynamically)."""
    return render(request, "bench/dashboard.html")

# --------------------------
#  API: ingest metrics
# --------------------------
@csrf_exempt
def api_ingest(request):
    """Receive novel CI/CD metrics from GitHub Actions, Jenkins, etc."""
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    # --- API key check ---
    api_key_header = (request.headers.get("X-Bench-Key") or "").strip()
    expected_key = (getattr(settings, "BENCH_API_KEY", "") or "").strip()

    if not expected_key:
        logger.error("BENCH_API_KEY missing in Django settings.")
        return JsonResponse({"error": "Server BENCH_API_KEY not configured"}, status=500)

    if api_key_header != expected_key:
        logger.warning("Unauthorized ingest attempt. Header=%r, Expected=%r", api_key_header, expected_key)
        return JsonResponse({"error": "Unauthorized"}, status=403)

    # --- Parse JSON body ---
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON payload")

    # Helper functions
    def get_metric_val(short_key, long_key):
        if short_key in payload:
            return payload.get(short_key)
        if long_key in payload:
            return payload.get(long_key)
        return 0.0

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

    logger.info("Stored new metric #%s for source=%s", metric.id, metric.source)
    return JsonResponse({"status": "stored", "id": metric.id, "created_at": metric.created_at.isoformat()})


# --------------------------
#  API: provide dashboard data
# --------------------------
def api_metrics_data(request):
    """Return aggregated metrics for dashboard charts."""
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

    metrics = list(qs.order_by("-created_at")[:100])
    metrics.reverse()  # chronological order

    rows = []
    lces, prts, smos, depts, clbcs = [], [], [], [], []

    for m in metrics:
        rows.append({
            "t": m.created_at.isoformat(),
            "lce": m.lce,
            "prt": m.prt,
            "smo": m.smo,
            "dept": m.dept,
            "clbc": m.clbc,
        })
        lces.append(m.lce)
        prts.append(m.prt)
        smos.append(m.smo)
        depts.append(m.dept)
        clbcs.append(m.clbc)

    def safe_avg(values):
        clean = [float(v) for v in values if v not in (None, "")]
        if not clean:
            return 0.0
        try:
            return round(statistics.fmean(clean), 2)
        except statistics.StatisticsError:
            return 0.0

    data = {
        "source": source,
        "count": len(metrics),
        "avg_lce": safe_avg(lces),
        "avg_prt": safe_avg(prts),
        "avg_smo": safe_avg(smos),
        "avg_dept": safe_avg(depts),
        "avg_clbc": safe_avg(clbcs),
        "rows": rows,
    }

    return JsonResponse(data)
