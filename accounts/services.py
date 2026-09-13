from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from audit.services import log_audit

from .kyc import get_kyc_provider
from .models import KYCSubmission, UserProfile
from .tokens import email_verification_token


def _send_branded_email(subject, template_prefix, context, recipient):
    text_body = render_to_string(f"emails/{template_prefix}.txt", context)
    html_body = render_to_string(f"emails/{template_prefix}.html", context)
    message = EmailMultiAlternatives(subject=subject, body=text_body, to=[recipient])
    message.attach_alternative(html_body, "text/html")
    message.send()


def send_verification_email(user, request):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = email_verification_token.make_token(user)
    path = reverse("verify_email", kwargs={"uidb64": uidb64, "token": token})
    link = request.build_absolute_uri(path)
    _send_branded_email(
        subject="Verify your VestNaija email address",
        template_prefix="verification_email",
        context={"display_name": user.first_name or user.email, "link": link},
        recipient=user.email,
    )


def send_kyc_status_email(user, *, approved, reason="", request=None):
    if request is not None:
        link = request.build_absolute_uri(reverse("kyc_submit"))
    else:
        link = reverse("kyc_submit")
    _send_branded_email(
        subject="You're verified on VestNaija" if approved else "Update on your VestNaija identity verification",
        template_prefix="kyc_status_email",
        context={"display_name": user.first_name or user.email, "approved": approved, "reason": reason, "link": link},
        recipient=user.email,
    )


def submit_kyc(user, cleaned_data):
    provider = get_kyc_provider()
    submission = provider.submit(user, cleaned_data)
    user.profile.kyc_status = UserProfile.KYCStatus.PENDING
    user.profile.save(update_fields=["kyc_status"])
    log_audit(user, "kyc_submitted", submission, {"id_type": submission.id_type})
    return submission


def review_kyc(submission, *, approve, reviewer, reason="", request=None):
    submission.status = KYCSubmission.Status.VERIFIED if approve else KYCSubmission.Status.REJECTED
    submission.reviewed_at = timezone.now()
    submission.reviewed_by = reviewer
    submission.rejection_reason = "" if approve else reason
    submission.save(update_fields=["status", "reviewed_at", "reviewed_by", "rejection_reason"])

    profile = submission.user.profile
    profile.kyc_status = UserProfile.KYCStatus.VERIFIED if approve else UserProfile.KYCStatus.REJECTED
    profile.save(update_fields=["kyc_status"])
    log_audit(reviewer, "kyc_reviewed", submission, {"approved": approve, "reason": reason})
    send_kyc_status_email(submission.user, approved=approve, reason=reason, request=request)
    return submission
