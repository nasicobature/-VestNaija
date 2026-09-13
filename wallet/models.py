import uuid
from django.conf import settings
from django.db import models
from django.db.models import Q


class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    available_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reserved_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_deposited = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} wallet"


class WalletTransaction(models.Model):
    class Type(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        WITHDRAWAL = "withdrawal", "Withdrawal"
        BUY_RESERVATION = "buy_reservation", "Buy Reservation"
        BUY_REFUND = "buy_refund", "Buy Refund"
        SALE_PROCEEDS = "sale_proceeds", "Sale Proceeds"
        FEE = "fee", "Fee"
        ADJUSTMENT = "adjustment", "Adjustment"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    type = models.CharField(max_length=32, choices=Type.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=64, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["type", "status"])]
        constraints = [models.CheckConstraint(condition=~Q(amount=0), name="wallet_tx_non_zero")]

    def __str__(self):
        return f"{self.type} {self.amount}"

# Create your models here.
