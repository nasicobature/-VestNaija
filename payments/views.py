import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Payment
from .services import confirm_deposit


@csrf_exempt
@require_POST
def flutterwave_webhook(request):
    signature = request.headers.get("verif-hash", "")
    if not settings.FLW_SECRET_HASH or signature != settings.FLW_SECRET_HASH:
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body or b"{}")
    except ValueError:
        return HttpResponseBadRequest("Invalid JSON")

    tx_ref = payload.get("data", {}).get("tx_ref")
    if not tx_ref:
        return HttpResponseBadRequest("Missing tx_ref")

    try:
        confirm_deposit(tx_ref)
    except Payment.DoesNotExist:
        return HttpResponse(status=404)

    return HttpResponse(status=200)


@login_required
def deposit_callback(request):
    reference = request.GET.get("tx_ref")
    if not reference:
        messages.error(request, "Missing payment reference.")
        return redirect("wallet")

    try:
        payment = confirm_deposit(reference)
    except Payment.DoesNotExist:
        messages.error(request, "We could not find that payment.")
        return redirect("wallet")

    if payment.status == Payment.Status.SUCCESSFUL:
        messages.success(request, "Deposit confirmed and credited to your wallet.")
    else:
        messages.error(request, "Payment was not successful.")
    return redirect("wallet")
