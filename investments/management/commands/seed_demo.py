from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from investments.models import Asset, IPO
from payments.services import simulate_deposit
from trading.models import FeeSchedule, TradingSetting
from wallet.services import get_or_create_wallet


class Command(BaseCommand):
    help = "Seed VestNaija demo data."

    def handle(self, *args, **options):
        today = timezone.now().date()
        assets = [
            {
                "symbol": "DANGREF",
                "name": "Dangote Petroleum Refinery & Petrochemicals",
                "current_price": Decimal("525.00"),
                "previous_price": Decimal("510.00"),
                "minimum_quantity": 10,
                "available_quantity": 500000,
                "status": Asset.Status.IPO_DEMO,
                "description": "Simulated IPO-style opportunity for product testing. Data is simulated and not an official offer.",
                "ipo": {"offer_price": Decimal("525.00"), "minimum_subscription": 10, "opens_at": today, "closes_at": today + timedelta(days=21)},
            },
            {
                "symbol": "MTNN",
                "name": "MTN Nigeria Communications",
                "current_price": Decimal("245.00"),
                "previous_price": Decimal("239.00"),
                "minimum_quantity": 1,
                "available_quantity": 100000,
                "status": Asset.Status.ACTIVE,
                "description": "Simulated equity card for marketplace and portfolio flows.",
            },
            {
                "symbol": "ZENITH",
                "name": "Zenith Bank Plc",
                "current_price": Decimal("48.50"),
                "previous_price": Decimal("47.10"),
                "minimum_quantity": 1,
                "available_quantity": 150000,
                "status": Asset.Status.ACTIVE,
                "description": "Simulated bank equity for sandbox trading.",
            },
            {
                "symbol": "BUAFOODS",
                "name": "BUA Foods Plc",
                "current_price": Decimal("410.00"),
                "previous_price": Decimal("395.00"),
                "minimum_quantity": 5,
                "available_quantity": 200000,
                "status": Asset.Status.IPO_DEMO,
                "description": "Simulated IPO-style opportunity for product testing. Data is simulated and not an official offer.",
                "ipo": {"offer_price": Decimal("410.00"), "minimum_subscription": 20, "opens_at": today, "closes_at": today + timedelta(days=14)},
            },
            {
                "symbol": "GEREGU",
                "name": "Geregu Power Plc",
                "current_price": Decimal("845.00"),
                "previous_price": Decimal("810.00"),
                "minimum_quantity": 5,
                "available_quantity": 120000,
                "status": Asset.Status.IPO_DEMO,
                "description": "Simulated IPO-style opportunity for product testing. Data is simulated and not an official offer.",
                "ipo": {"offer_price": Decimal("845.00"), "minimum_subscription": 10, "opens_at": today + timedelta(days=7), "closes_at": today + timedelta(days=28)},
            },
            {
                "symbol": "TRANSPWR",
                "name": "Transcorp Power Plc",
                "current_price": Decimal("298.00"),
                "previous_price": Decimal("275.00"),
                "minimum_quantity": 5,
                "available_quantity": 180000,
                "status": Asset.Status.IPO_DEMO,
                "description": "Simulated IPO-style opportunity for product testing. Data is simulated and not an official offer.",
                "ipo": {"offer_price": Decimal("298.00"), "minimum_subscription": 15, "opens_at": today, "closes_at": today + timedelta(days=10)},
            },
        ]
        for data in assets:
            ipo_terms = data.pop("ipo", None)
            asset, _ = Asset.objects.update_or_create(symbol=data["symbol"], defaults={**data, "market": "NGX", "is_demo_data": True, "is_enabled": True})
            if ipo_terms:
                IPO.objects.update_or_create(asset=asset, defaults={**ipo_terms, "status": "IPO / Simulated"})

        FeeSchedule.objects.update_or_create(name="Standard brokerage fee", defaults={"rate": Decimal("0.00500"), "is_active": True, "notes": "Configurable placeholder; not an official fee schedule."})
        TradingSetting.objects.update_or_create(key="trading_mode", defaults={"value": "simulated", "description": "No real securities are traded; asset prices are simulated."})

        user, created = User.objects.get_or_create(username="nasir@example.com", defaults={"email": "nasir@example.com", "first_name": "Nasir", "last_name": ""})
        if created:
            user.set_password("DemoPass123!")
            user.save()
            user.profile.phone = "+2348012345678"
            user.profile.accepted_terms = True
            user.profile.save()
        get_or_create_wallet(user)
        if user.wallet.total_deposited == 0:
            simulate_deposit(user, Decimal("250000.00"))
        self.stdout.write(self.style.SUCCESS("VestNaija demo data seeded. Demo login: nasir@example.com / DemoPass123!"))
