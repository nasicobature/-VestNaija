from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from investments.models import Asset, IPO
from payments.services import simulate_deposit
from trading.models import FeeSchedule, TradingSetting
from wallet.services import get_or_create_wallet

SIMULATED_NOTE = "Simulated equity card for marketplace and portfolio flows. Data is simulated and not an official offer."
IPO_NOTE = "Simulated IPO-style opportunity for product testing. Data is simulated and not an official offer."


class Command(BaseCommand):
    help = "Seed VestNaija demo data."

    def handle(self, *args, **options):
        today = timezone.now().date()
        assets = [
            # --- Banking ---
            {
                "symbol": "ZENITH",
                "name": "Zenith Bank Plc",
                "sector": Asset.Sector.BANKING,
                "current_price": Decimal("48.50"),
                "previous_price": Decimal("47.10"),
                "minimum_quantity": 1,
                "available_quantity": 150000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "GTCO",
                "name": "Guaranty Trust Holding Company Plc",
                "sector": Asset.Sector.BANKING,
                "current_price": Decimal("62.80"),
                "previous_price": Decimal("60.35"),
                "minimum_quantity": 1,
                "available_quantity": 140000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "ACCESSCORP",
                "name": "Access Holdings Plc",
                "sector": Asset.Sector.BANKING,
                "current_price": Decimal("24.10"),
                "previous_price": Decimal("23.40"),
                "minimum_quantity": 1,
                "available_quantity": 200000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "UBA",
                "name": "United Bank for Africa Plc",
                "sector": Asset.Sector.BANKING,
                "current_price": Decimal("31.55"),
                "previous_price": Decimal("30.20"),
                "minimum_quantity": 1,
                "available_quantity": 175000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "FBNH",
                "name": "FBN Holdings Plc",
                "sector": Asset.Sector.BANKING,
                "current_price": Decimal("29.85"),
                "previous_price": Decimal("28.90"),
                "minimum_quantity": 1,
                "available_quantity": 160000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "STANBIC",
                "name": "Stanbic IBTC Holdings Plc",
                "sector": Asset.Sector.BANKING,
                "current_price": Decimal("68.00"),
                "previous_price": Decimal("65.50"),
                "minimum_quantity": 1,
                "available_quantity": 80000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Telecommunications ---
            {
                "symbol": "MTNN",
                "name": "MTN Nigeria Communications Plc",
                "sector": Asset.Sector.TELECOM,
                "current_price": Decimal("245.00"),
                "previous_price": Decimal("239.00"),
                "minimum_quantity": 1,
                "available_quantity": 100000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "AIRTELAFRI",
                "name": "Airtel Africa Plc",
                "sector": Asset.Sector.TELECOM,
                "current_price": Decimal("2150.00"),
                "previous_price": Decimal("2080.00"),
                "minimum_quantity": 1,
                "available_quantity": 40000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Consumer Goods ---
            {
                "symbol": "NESTLE",
                "name": "Nestle Nigeria Plc",
                "sector": Asset.Sector.CONSUMER_GOODS,
                "current_price": Decimal("1450.00"),
                "previous_price": Decimal("1390.00"),
                "minimum_quantity": 1,
                "available_quantity": 25000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "NB",
                "name": "Nigerian Breweries Plc",
                "sector": Asset.Sector.CONSUMER_GOODS,
                "current_price": Decimal("41.20"),
                "previous_price": Decimal("39.80"),
                "minimum_quantity": 1,
                "available_quantity": 120000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "UNILEVER",
                "name": "Unilever Nigeria Plc",
                "sector": Asset.Sector.CONSUMER_GOODS,
                "current_price": Decimal("38.90"),
                "previous_price": Decimal("36.50"),
                "minimum_quantity": 1,
                "available_quantity": 90000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "FLOURMILL",
                "name": "Flour Mills of Nigeria Plc",
                "sector": Asset.Sector.CONSUMER_GOODS,
                "current_price": Decimal("58.75"),
                "previous_price": Decimal("55.00"),
                "minimum_quantity": 1,
                "available_quantity": 100000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "BUAFOODS",
                "name": "BUA Foods Plc",
                "sector": Asset.Sector.CONSUMER_GOODS,
                "current_price": Decimal("410.00"),
                "previous_price": Decimal("395.00"),
                "minimum_quantity": 5,
                "available_quantity": 200000,
                "status": Asset.Status.IPO_DEMO,
                "ipo": {"offer_price": Decimal("410.00"), "minimum_subscription": 20, "opens_at": today, "closes_at": today + timedelta(days=14)},
            },
            # --- Industrial Goods ---
            {
                "symbol": "DANGCEM",
                "name": "Dangote Cement Plc",
                "sector": Asset.Sector.INDUSTRIAL,
                "current_price": Decimal("495.00"),
                "previous_price": Decimal("478.00"),
                "minimum_quantity": 1,
                "available_quantity": 60000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "WAPCO",
                "name": "Lafarge Africa Plc",
                "sector": Asset.Sector.INDUSTRIAL,
                "current_price": Decimal("72.30"),
                "previous_price": Decimal("69.10"),
                "minimum_quantity": 1,
                "available_quantity": 110000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "BUACEMENT",
                "name": "BUA Cement Plc",
                "sector": Asset.Sector.INDUSTRIAL,
                "current_price": Decimal("115.00"),
                "previous_price": Decimal("108.50"),
                "minimum_quantity": 1,
                "available_quantity": 95000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "DANGREF",
                "name": "Dangote Petroleum Refinery & Petrochemicals",
                "sector": Asset.Sector.OIL_GAS,
                "current_price": Decimal("525.00"),
                "previous_price": Decimal("510.00"),
                "minimum_quantity": 10,
                "available_quantity": 500000,
                "status": Asset.Status.IPO_DEMO,
                "ipo": {"offer_price": Decimal("525.00"), "minimum_subscription": 10, "opens_at": today, "closes_at": today + timedelta(days=21)},
            },
            # --- Oil & Gas ---
            {
                "symbol": "SEPLAT",
                "name": "Seplat Energy Plc",
                "sector": Asset.Sector.OIL_GAS,
                "current_price": Decimal("4850.00"),
                "previous_price": Decimal("4620.00"),
                "minimum_quantity": 1,
                "available_quantity": 20000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "TOTAL",
                "name": "TotalEnergies Marketing Nigeria Plc",
                "sector": Asset.Sector.OIL_GAS,
                "current_price": Decimal("620.00"),
                "previous_price": Decimal("595.00"),
                "minimum_quantity": 1,
                "available_quantity": 30000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "CONOIL",
                "name": "Conoil Plc",
                "sector": Asset.Sector.OIL_GAS,
                "current_price": Decimal("142.00"),
                "previous_price": Decimal("133.50"),
                "minimum_quantity": 1,
                "available_quantity": 45000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Insurance ---
            {
                "symbol": "AIICO",
                "name": "AIICO Insurance Plc",
                "sector": Asset.Sector.INSURANCE,
                "current_price": Decimal("1.85"),
                "previous_price": Decimal("1.72"),
                "minimum_quantity": 100,
                "available_quantity": 800000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "NEM",
                "name": "NEM Insurance Plc",
                "sector": Asset.Sector.INSURANCE,
                "current_price": Decimal("6.40"),
                "previous_price": Decimal("5.95"),
                "minimum_quantity": 10,
                "available_quantity": 400000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Agriculture ---
            {
                "symbol": "PRESCO",
                "name": "Presco Plc",
                "sector": Asset.Sector.AGRICULTURE,
                "current_price": Decimal("685.00"),
                "previous_price": Decimal("650.00"),
                "minimum_quantity": 1,
                "available_quantity": 35000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "OKOMUOIL",
                "name": "The Okomu Oil Palm Company Plc",
                "sector": Asset.Sector.AGRICULTURE,
                "current_price": Decimal("560.00"),
                "previous_price": Decimal("525.00"),
                "minimum_quantity": 1,
                "available_quantity": 28000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Conglomerates ---
            {
                "symbol": "TRANSCORP",
                "name": "Transnational Corporation Plc",
                "sector": Asset.Sector.CONGLOMERATE,
                "current_price": Decimal("18.60"),
                "previous_price": Decimal("17.10"),
                "minimum_quantity": 10,
                "available_quantity": 300000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "UACN",
                "name": "UAC of Nigeria Plc",
                "sector": Asset.Sector.CONGLOMERATE,
                "current_price": Decimal("29.40"),
                "previous_price": Decimal("27.80"),
                "minimum_quantity": 1,
                "available_quantity": 85000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Utilities & Power (IPO opportunities) ---
            {
                "symbol": "GEREGU",
                "name": "Geregu Power Plc",
                "sector": Asset.Sector.UTILITIES,
                "current_price": Decimal("845.00"),
                "previous_price": Decimal("810.00"),
                "minimum_quantity": 5,
                "available_quantity": 120000,
                "status": Asset.Status.IPO_DEMO,
                "ipo": {"offer_price": Decimal("845.00"), "minimum_subscription": 10, "opens_at": today + timedelta(days=7), "closes_at": today + timedelta(days=28)},
            },
            {
                "symbol": "TRANSPWR",
                "name": "Transcorp Power Plc",
                "sector": Asset.Sector.UTILITIES,
                "current_price": Decimal("298.00"),
                "previous_price": Decimal("275.00"),
                "minimum_quantity": 5,
                "available_quantity": 180000,
                "status": Asset.Status.IPO_DEMO,
                "ipo": {"offer_price": Decimal("298.00"), "minimum_subscription": 15, "opens_at": today, "closes_at": today + timedelta(days=10)},
            },
            # --- Healthcare ---
            {
                "symbol": "FIDSON",
                "name": "Fidson Healthcare Plc",
                "sector": Asset.Sector.HEALTHCARE,
                "current_price": Decimal("18.90"),
                "previous_price": Decimal("17.40"),
                "minimum_quantity": 10,
                "available_quantity": 150000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "MAYBAKER",
                "name": "May & Baker Nigeria Plc",
                "sector": Asset.Sector.HEALTHCARE,
                "current_price": Decimal("9.85"),
                "previous_price": Decimal("8.90"),
                "minimum_quantity": 10,
                "available_quantity": 130000,
                "status": Asset.Status.ACTIVE,
            },
            # --- Real Estate & Construction ---
            {
                "symbol": "UPDC",
                "name": "UPDC Plc",
                "sector": Asset.Sector.REAL_ESTATE,
                "current_price": Decimal("2.35"),
                "previous_price": Decimal("2.10"),
                "minimum_quantity": 100,
                "available_quantity": 900000,
                "status": Asset.Status.ACTIVE,
            },
            {
                "symbol": "JBERGER",
                "name": "Julius Berger Nigeria Plc",
                "sector": Asset.Sector.REAL_ESTATE,
                "current_price": Decimal("104.00"),
                "previous_price": Decimal("96.50"),
                "minimum_quantity": 1,
                "available_quantity": 70000,
                "status": Asset.Status.ACTIVE,
            },
        ]
        for data in assets:
            ipo_terms = data.pop("ipo", None)
            is_ipo = data["status"] == Asset.Status.IPO_DEMO
            data.setdefault("description", IPO_NOTE if is_ipo else SIMULATED_NOTE)
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
        self.stdout.write(self.style.SUCCESS(f"VestNaija demo data seeded with {len(assets)} listings. Demo login: nasir@example.com / DemoPass123!"))
