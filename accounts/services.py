from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from audit.services import log_audit

from .kyc import get_kyc_provider
from .models import KYCSubmission, UserProfile
from .tokens import email_verification_token


def send_verification_email(user, request):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    path = reverse("verify_email", kwargs={"uidb64": uidb64, "token": token})
    link = request.build_absolute_uri(path)
    send_mail(
        subject="Verify your VestNaija email address",
        message=(
            f"Hi {user.first_name or user.email},\n\n"
            f"Confirm your email address by opening this link:\n{link}\n\n"
            "If you did not create this account, you can ignore this email."
        ),
        from_email=None,
        recipient_list=[user.email],
    )


def submit_kyc(user, cleaned_data):
    provider = get_kyc_provider()
    submission = provider.submit(user, cleaned_data)
    user.profile.kyc_status = UserProfile.KYCStatus.PENDING
    user.profile.save(update_fields=["kyc_status"])
    log_audit(user, "kyc_submitted", submission, {"id_type": submission.id_type})
    return submission


def review_kyc(submission, *, approve, reviewer, reason=""):
    submission.status = KYCSubmission.Status.VERIFIED if approve else KYCSubmission.Status.REJECTED
    submission.reviewed_at = timezone.now()
    submission.reviewed_by = reviewer
    submission.rejection_reason = "" if approve else reason
    submission.save(update_fields=["status", "reviewed_at", "reviewed_by", "rejection_reason"])

    profile = submission.user.profile
    profile.kyc_status = UserProfile.KYCStatus.VERIFIED if approve else UserProfile.KYCStatus.REJECTED
    profile.save(update_fields=["kyc_status"])
    log_audit(reviewer, "kyc_reviewed", submission, {"approved": approve, "reason": reason})
    return submission
