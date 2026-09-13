from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    class KYCStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        PENDING = "pending", "Pending Review"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=24, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    account_status = models.CharField(max_length=32, default="Active")
    kyc_status = models.CharField(max_length=24, choices=KYCStatus.choices, default=KYCStatus.NOT_STARTED)
    email_verification_placeholder = models.BooleanField(default=False)
    accepted_terms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class KYCSubmission(models.Model):
    class IDType(models.TextChoices):
        BVN = "bvn", "Bank Verification Number (BVN)"
        NIN = "nin", "National Identity Number (NIN)"
        PASSPORT = "passport", "International Passport"
        DRIVERS_LICENSE = "drivers_license", "Driver's License"
        VOTERS_CARD = "voters_card", "Voter's Card"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Review"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="kyc_submissions")
    full_name = models.CharField(max_length=160)
    date_of_birth = models.DateField()
    id_type = models.CharField(max_length=20, choices=IDType.choices)
    id_number = models.CharField(max_length=32)
    id_document = models.FileField(upload_to="kyc/documents/")
    selfie = models.ImageField(upload_to="kyc/selfies/", blank=True, null=True)
    address = models.TextField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.CharField(max_length=255, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="kyc_reviews"
    )

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.user.email} KYC ({self.get_status_display()})"


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
