from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse

from accounts.models import UserProfile
from payments.services import initiate_deposit, simulate_deposit, simulate_withdrawal
from portfolio.services import portfolio_summary

from .forms import DepositForm, WithdrawalForm
from .services import get_or_create_wallet


@login_required
def wallet_home(request):
    wallet = get_or_create_wallet(request.user)
    return render(request, "wallet/home.html", {"wallet": wallet, "summary": portfolio_summary(request.user)})


@login_required
def deposit(request):
    live_provider = (settings.PAYMENT_PROVIDER or "mock").lower().startswith("flutterwave")
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            if live_provider:
                redirect_url = request.build_absolute_uri(reverse("deposit_callback"))
                payment = initiate_deposit(request.user, amount, redirect_url=redirect_url)
                if payment.checkout_url:
                    return redirect(payment.checkout_url)
                messages.error(request, "Unable to start payment right now. Please try again.")
            else:
                simulate_deposit(request.user, amount)
                messages.success(request, "Demo deposit completed. No real money moved.")
                return redirect("wallet")
    else:
        form = DepositForm()
    return render(request, "wallet/deposit.html", {"form": form, "live_provider": live_provider})


@login_required
def withdraw(request):
    live_provider = (settings.PAYMENT_PROVIDER or "mock").lower().startswith("flutterwave")
    kyc_required = live_provider and request.user.profile.kyc_status != UserProfile.KYCStatus.VERIFIED
    if kyc_required:
        messages.error(request, "Verify your identity before withdrawing real funds.")
        return redirect("kyc_submit")

    if request.method == "POST":
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            try:
                simulate_withdrawal(request.user, **form.cleaned_data)
                messages.success(
                    request,
                    "Withdrawal request received. Payouts are reviewed and sent manually for now — "
                    "there is no automatic bank transfer connected yet.",
                )
                return redirect("wallet")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = WithdrawalForm()
    return render(request, "wallet/withdraw.html", {"form": form})


@login_required
def transactions(request):
    wallet = get_or_create_wallet(request.user)
    kind = request.GET.get("type", "all")
    transactions = wallet.transactions.all()
    if kind != "all":
        transactions = transactions.filter(type=kind)
    return render(request, "wallet/transactions.html", {"transactions": transactions, "kind": kind})

# Create your views here.
