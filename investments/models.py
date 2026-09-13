from django.db import models


class Asset(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        IPO_DEMO = "ipo_demo", "IPO / Simulated"
        NOT_LISTED = "not_listed", "Not Listed"
        DISABLED = "disabled", "Disabled"

    class Sector(models.TextChoices):
        BANKING = "banking", "Banking"
        TELECOM = "telecom", "Telecommunications"
        CONSUMER_GOODS = "consumer_goods", "Consumer Goods"
        INDUSTRIAL = "industrial", "Industrial Goods"
        OIL_GAS = "oil_gas", "Oil & Gas"
        INSURANCE = "insurance", "Insurance"
        AGRICULTURE = "agriculture", "Agriculture"
        CONGLOMERATE = "conglomerate", "Conglomerates"
        HEALTHCARE = "healthcare", "Healthcare"
        REAL_ESTATE = "real_estate", "Real Estate & Construction"
        UTILITIES = "utilities", "Utilities & Power"

    name = models.CharField(max_length=160)
    symbol = models.CharField(max_length=24, unique=True)
    market = models.CharField(max_length=32, default="NGX")
    sector = models.CharField(max_length=32, choices=Sector.choices, blank=True)
    description = models.TextField()
    current_price = models.DecimalField(max_digits=18, decimal_places=2)
    previous_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    minimum_quantity = models.PositiveIntegerField(default=1)
    available_quantity = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.IPO_DEMO)
    is_demo_data = models.BooleanField(default=True, verbose_name="synthetic data")
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
    status = models.CharField(max_length=32, default="Simulated subscription")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def minimum_investment(self):
        return self.offer_price * self.minimum_subscription

    def __str__(self):
        return f"{self.asset.symbol} IPO"

# Create your models here.
