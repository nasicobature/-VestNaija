from django.utils import timezone

from audit.services import log_audit

from .kyc import get_kyc_provider
from .models import KYCSubmission, UserProfile


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
