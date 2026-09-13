from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from investments.models import Asset
from portfolio.services import portfolio_summary
from wallet.services import get_or_create_wallet

from .forms import EmailLoginForm, KYCSubmissionForm, RegistrationForm
from .models import KYCSubmission, UserProfile
from .services import send_verification_email, submit_kyc
from .tokens import email_verification_token


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
            send_verification_email(user, request)
            messages.success(request, "Welcome to VestNaija. Check your email to verify your address.")
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
    latest_kyc = request.user.kyc_submissions.first()
    return render(request, "accounts/profile.html", {"latest_kyc": latest_kyc})


@login_required
def kyc_submit(request):
    profile = request.user.profile
    latest = request.user.kyc_submissions.first()

    if profile.kyc_status == UserProfile.KYCStatus.VERIFIED:
        messages.info(request, "Your identity is already verified.")
        return redirect("profile")
    if latest and latest.status == KYCSubmission.Status.PENDING:
        messages.info(request, "Your identity documents are already under review.")
        return redirect("profile")
    if not profile.email_verified:
        messages.error(request, "Please verify your email address before starting identity verification.")
        return redirect("profile")

    if request.method == "POST":
        form = KYCSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submit_kyc(request.user, form.cleaned_data)
            messages.success(request, "Identity documents submitted. We'll review them shortly.")
            return redirect("profile")
    else:
        form = KYCSubmissionForm()
    return render(request, "accounts/kyc_submit.html", {"form": form, "latest": latest})


def verify_email(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        if not user.profile.email_verified:
            user.profile.email_verified = True
            user.profile.email_verified_at = timezone.now()
            user.profile.save(update_fields=["email_verified", "email_verified_at"])
        messages.success(request, "Your email address is verified.")
    else:
        messages.error(request, "That verification link is invalid or has expired.")
    return redirect("profile" if request.user.is_authenticated else "login")


@login_required
def resend_verification(request):
    if request.user.profile.email_verified:
        messages.info(request, "Your email is already verified.")
    else:
        send_verification_email(request.user, request)
        messages.success(request, "Verification email sent. Check your inbox.")
    return redirect("profile")
