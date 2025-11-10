from django.http import JsonResponse, HttpResponse


def health(request):
    """
    Simple health-check endpoint for load balancers / uptime checks.
    """
    return JsonResponse({"status": "ok"})


def index(request):
    """
    Basic text response to confirm the app is running.
    """
    return HttpResponse("CI/CD Benchmark app is running ✅")
