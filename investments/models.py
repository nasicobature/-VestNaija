from django.db import models


class Asset(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        IPO_DEMO = "ipo_demo", "IPO / Demo"
        DISABLED = "disabled", "Disabled"

    name = models.CharField(max_length=160)
    symbol = models.CharField(max_length=24, unique=True)
    market = models.CharField(max_length=32, default="NGX")
    description = models.TextField()
    current_price = models.DecimalField(max_digits=18, decimal_places=2)
    previous_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    minimum_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IPO_DEMO)
    is_demo_data = models.BooleanField(default=True)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["symbol"]
        indexes = [models.Index(fields=["symbol", "status"])]

    @property
    def price_change(self):
        return self.current_price - self.previous_price

    def __str__(self):
        return f"{self.symbol} - {self.name}"


class IPO(models.Model):
    asset = models.OneToOneField(Asset, on_delete=models.CASCADE, related_name="ipo")
    offer_price = models.DecimalField(max_digits=18, decimal_places=2)
    minimum_subscription = models.PositiveIntegerField(default=10)
    opens_at = models.DateField(blank=True, null=True)
    closes_at = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=32, default="Demo subscription")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.symbol} IPO"

# Create your models here.
