import uuid
from django.conf import settings
from django.db import models


class Holding(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="holdings")
    asset = models.ForeignKey("investments.Asset", on_delete=models.PROTECT, related_name="holdings")
    quantity = models.PositiveIntegerField(default=0)
    average_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "asset")
        indexes = [models.Index(fields=["user", "asset"])]

    def __str__(self):
        return f"{self.user.email} {self.asset.symbol}"

    @property
    def current_value(self):
        return self.quantity * self.asset.current_price

    @property
    def profit_loss(self):
        return self.current_value - (self.quantity * self.average_price)


class Order(models.Model):
    class Side(models.TextChoices):
        BUY = "buy", "Buy"
        SELL = "sell", "Sell"

    class OrderType(models.TextChoices):
        MARKET = "market", "Market"
        LIMIT = "limit", "Limit"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PARTIALLY_FILLED = "partially_filled", "Partially Filled"
        FILLED = "filled", "Filled"
        CANCELLED = "cancelled", "Cancelled"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders")
    asset = models.ForeignKey("investments.Asset", on_delete=models.PROTECT, related_name="orders")
    side = models.CharField(max_length=8, choices=Side.choices)
    order_type = models.CharField(max_length=12, choices=OrderType.choices)
    quantity = models.PositiveIntegerField()
    filled_quantity = models.PositiveIntegerField(default=0)
    limit_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    execution_price = models.DecimalField(max_digits=18, decimal_places=2, blank=True, null=True)
    estimated_fee = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reserved_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    executed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "status", "side"])]

    def __str__(self):
        return f"{self.side} {self.quantity} {self.asset.symbol}"


class Trade(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="trades")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="trades")
    asset = models.ForeignKey("investments.Asset", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=18, decimal_places=2)
    gross_amount = models.DecimalField(max_digits=18, decimal_places=2)
    fee = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class FeeSchedule(models.Model):
    name = models.CharField(max_length=80, unique=True)
    rate = models.DecimalField(max_digits=8, decimal_places=5, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TradingSetting(models.Model):
    key = models.CharField(max_length=80, unique=True)
    value = models.CharField(max_length=160)
    description = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key

# Create your models here.
