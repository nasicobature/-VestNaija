from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    class KYCStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        PENDING = "pending", "Pending"
        DEMO_ONLY = "demo_only", "Demo Only"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=24, blank=True)
    profile_picture = models.ImageField(upload_to="profiles/", blank=True, null=True)
    account_status = models.CharField(max_length=32, default="Demo Active")
    kyc_status = models.CharField(max_length=24, choices=KYCStatus.choices, default=KYCStatus.DEMO_ONLY)
    email_verification_placeholder = models.BooleanField(default=False)
    accepted_terms = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.email


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)

# Create your models here.
