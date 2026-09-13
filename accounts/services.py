import secrets
from datetime import timedelta

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

KYC_APPROVAL_EMAIL_DELAY = timedelta(hours=24)


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


def review_kyc(submission, *, approve, reviewer, reason=""):
    submission.status = KYCSubmission.Status.VERIFIED if approve else KYCSubmission.Status.REJECTED
    submission.reviewed_at = timezone.now()
    submission.reviewed_by = reviewer
    submission.rejection_reason = "" if approve else reason
    update_fields = ["status", "reviewed_at", "reviewed_by", "rejection_reason"]
    if approve:
        submission.approval_email_due_at = timezone.now() + KYC_APPROVAL_EMAIL_DELAY
        update_fields.append("approval_email_due_at")
    submission.save(update_fields=update_fields)

    profile = submission.user.profile
    profile.kyc_status = UserProfile.KYCStatus.VERIFIED if approve else UserProfile.KYCStatus.REJECTED
    profile.save(update_fields=["kyc_status"])
    log_audit(reviewer, "kyc_reviewed", submission, {"approved": approve, "reason": reason})
    return submission


def send_due_kyc_approval_emails():
    """Send the queued 'you're verified' email once its 24-hour delay has elapsed.

    Meant to be run periodically (e.g. a scheduled task/cron job calling the
    send_due_kyc_emails management command) since this app has no background
    task queue.
    """
    due = KYCSubmission.objects.filter(
        status=KYCSubmission.Status.VERIFIED,
        approval_email_due_at__lte=timezone.now(),
        approval_email_sent_at__isnull=True,
    )
    sent = 0
    for submission in due:
        send_kyc_status_email(submission.user, approved=True)
        submission.approval_email_sent_at = timezone.now()
        submission.save(update_fields=["approval_email_sent_at"])
        sent += 1
    return sent


def generate_login_key():
    return secrets.token_urlsafe(24)


def ensure_login_key(profile):
    if not profile.login_key:
        profile.login_key = generate_login_key()
        profile.save(update_fields=["login_key"])
    return profile.login_key


def regenerate_login_key(profile):
    profile.login_key = generate_login_key()
    profile.save(update_fields=["login_key"])
    return profile.login_key
