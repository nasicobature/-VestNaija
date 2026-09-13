import uuid
from django.conf import settings
from django.db import models


def payment_reference():
    return f"DEP-{uuid.uuid4().hex[:10].upper()}"


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESSFUL = "successful", "Successful"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    reference = models.CharField(max_length=64, unique=True, default=payment_reference)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=64, default="mock")
    provider_transaction_id = models.CharField(max_length=96, blank=True, null=True, unique=True)
    checkout_url = models.URLField(blank=True)
    credited_at = models.DateTimeField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(blank=True, null=True)

    @property
    def verification_status(self):
        if self.credited_at:
            return "Verified and credited"
        if self.verified_at:
            return "Verified, not credited"
        return "Unverified"


class Deposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="deposits")
    payment = models.OneToOneField(Payment, on_delete=models.PROTECT, related_name="deposit")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=3, default="NGN")
    status = models.CharField(max_length=16, choices=Payment.Status.choices, default=Payment.Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)


class Withdrawal(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="withdrawals")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    bank = models.CharField(max_length=120)
    account_number = models.CharField(max_length=20)
    account_name = models.CharField(max_length=160)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

# Create your models here.
