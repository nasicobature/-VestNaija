from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from payments.services import simulate_deposit, simulate_withdrawal
from portfolio.services import portfolio_summary

from .forms import DepositForm, WithdrawalForm
from .services import get_or_create_wallet


@login_required
def wallet_home(request):
    wallet = get_or_create_wallet(request.user)
    return render(request, "wallet/home.html", {"wallet": wallet, "summary": portfolio_summary(request.user)})


@login_required
def deposit(request):
    if request.method == "POST":
        form = DepositForm(request.POST)
        if form.is_valid():
            simulate_deposit(request.user, form.cleaned_data["amount"])
            messages.success(request, "Demo deposit completed. No real money moved.")
            return redirect("wallet")
    else:
        form = DepositForm()
    return render(request, "wallet/deposit.html", {"form": form})


@login_required
def withdraw(request):
    if request.method == "POST":
        form = WithdrawalForm(request.POST)
        if form.is_valid():
            try:
                simulate_withdrawal(request.user, **form.cleaned_data)
                messages.success(request, "Demo withdrawal request created.")
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
