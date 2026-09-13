from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render

from investments.models import Asset
from portfolio.services import portfolio_summary
from wallet.services import get_or_create_wallet

from .forms import EmailLoginForm, RegistrationForm


def landing(request):
    assets = Asset.objects.filter(is_enabled=True)[:3]
    return render(request, "landing.html", {"assets": assets})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            get_or_create_wallet(user)
            login(request, user)
            messages.success(request, "Welcome to VestNaija demo mode.")
            return redirect("dashboard")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


class VestLoginView(LoginView):
    authentication_form = EmailLoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        if not self.request.POST.get("remember"):
            self.request.session.set_expiry(0)
        return super().form_valid(form)


class VestLogoutView(LogoutView):
    pass


@login_required
def dashboard(request):
    wallet = get_or_create_wallet(request.user)
    summary = portfolio_summary(request.user)
    return render(
        request,
        "dashboard.html",
        {
            "wallet": wallet,
            "summary": summary,
            "assets": Asset.objects.filter(is_enabled=True)[:4],
            "orders": request.user.orders.select_related("asset")[:5],
            "transactions": wallet.transactions.all()[:5],
        },
    )


@login_required
def profile(request):
    return render(request, "accounts/profile.html")
