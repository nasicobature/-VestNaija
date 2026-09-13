import hmac

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound

from .services import send_due_kyc_approval_emails


def run_kyc_emails(request):
    """Secret-protected trigger for send_due_kyc_approval_emails.

    Exists because the platform's cron job (render.yaml) requires a paid
    Render plan; on the free tier this endpoint is polled instead by the
    repo's GitHub Actions scheduled workflow.
    """
    if not settings.CRON_SECRET:
        return HttpResponseNotFound()

    token = request.headers.get("X-Cron-Token", "")
    if not hmac.compare_digest(token, settings.CRON_SECRET):
        return HttpResponseForbidden()

    sent = send_due_kyc_approval_emails()
    return HttpResponse(f"sent={sent}")
