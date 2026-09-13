from django.contrib import admin, messages
from django.utils.html import format_html

from .models import KYCSubmission, UserProfile
from .services import review_kyc


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "account_status", "kyc_status", "email_verified", "created_at")
    list_filter = ("kyc_status", "account_status", "email_verified")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone")


@admin.register(KYCSubmission)
class KYCSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "id_type", "status", "submitted_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "id_type")
    search_fields = ("user__email", "full_name", "id_number")
    date_hierarchy = "submitted_at"
    readonly_fields = (
        "user",
        "full_name",
        "date_of_birth",
        "id_type",
        "id_number",
        "id_document",
        "document_preview",
        "selfie",
        "selfie_preview",
        "address",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "approval_email_due_at",
        "approval_email_sent_at",
    )
    fields = (
        "user",
        "full_name",
        "date_of_birth",
        "id_type",
        "id_number",
        "id_document",
        "document_preview",
        "selfie",
        "selfie_preview",
        "address",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "status",
        "rejection_reason",
        "approval_email_due_at",
        "approval_email_sent_at",
    )
    actions = ["approve_selected", "reject_selected"]

    @admin.display(description="Document preview")
    def document_preview(self, obj):
        if not obj.id_document:
            return "-"
        name = obj.id_document.name.lower()
        if name.endswith(".pdf"):
            return format_html('<a href="{}" target="_blank" rel="noopener">Open PDF document</a>', obj.id_document.url)
        return format_html('<img src="{}" style="max-width:320px;max-height:320px;border-radius:8px;">', obj.id_document.url)

    @admin.display(description="Selfie preview")
    def selfie_preview(self, obj):
        if not obj.selfie:
            return "-"
        return format_html('<img src="{}" style="max-width:220px;max-height:220px;border-radius:8px;">', obj.selfie.url)

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data and obj.status in (
            KYCSubmission.Status.VERIFIED,
            KYCSubmission.Status.REJECTED,
        ):
            if obj.status == KYCSubmission.Status.REJECTED and not obj.rejection_reason.strip():
                self.message_user(request, "A rejection reason is required when rejecting a submission.", level=messages.ERROR)
                return
            review_kyc(
                obj,
                approve=obj.status == KYCSubmission.Status.VERIFIED,
                reviewer=request.user,
                reason=obj.rejection_reason,
            )
        else:
            super().save_model(request, obj, form, change)

    @admin.action(description="Approve selected KYC submissions")
    def approve_selected(self, request, queryset):
        for submission in queryset.filter(status=KYCSubmission.Status.PENDING):
            review_kyc(submission, approve=True, reviewer=request.user)

    @admin.action(description="Reject selected KYC submissions")
    def reject_selected(self, request, queryset):
        for submission in queryset.filter(status=KYCSubmission.Status.PENDING):
            review_kyc(submission, approve=False, reviewer=request.user, reason="Rejected via bulk admin action.")
