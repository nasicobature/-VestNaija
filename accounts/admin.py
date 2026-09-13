from django.contrib import admin

from .models import KYCSubmission, UserProfile
from .services import review_kyc


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "account_status", "kyc_status", "created_at")
    list_filter = ("kyc_status", "account_status")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone")


@admin.register(KYCSubmission)
class KYCSubmissionAdmin(admin.ModelAdmin):
    list_display = ("user", "full_name", "id_type", "status", "submitted_at", "reviewed_at", "reviewed_by")
    list_filter = ("status", "id_type")
    search_fields = ("user__email", "full_name", "id_number")
    readonly_fields = (
        "user",
        "full_name",
        "date_of_birth",
        "id_type",
        "id_number",
        "id_document",
        "selfie",
        "address",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
    )
    fields = readonly_fields + ("status", "rejection_reason")
    actions = ["approve_selected", "reject_selected"]

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data and obj.status in (
            KYCSubmission.Status.VERIFIED,
            KYCSubmission.Status.REJECTED,
        ):
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
