from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from investments.models import Asset
from payments.services import simulate_deposit, simulate_withdrawal
from portfolio.services import portfolio_summary
from trading.models import Holding, Order
from trading.services import cancel_order, create_order
from wallet.models import Wallet, WalletTransaction


class VestNaijaFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada@example.com", email="ada@example.com", password="StrongPass123!", first_name="Ada")
        self.other = User.objects.create_user(username="other@example.com", email="other@example.com", password="StrongPass123!")
        self.asset = Asset.objects.create(
            name="Dangote Petroleum Refinery & Petrochemicals",
            symbol="DANGREF",
            market="NGX",
            description="Demo data",
            current_price=Decimal("525.00"),
            previous_price=Decimal("510.00"),
            minimum_quantity=10,
            available_quantity=100000,
            status=Asset.Status.IPO_DEMO,
        )

    def test_registration_creates_profile_wallet_and_login_session(self):
        response = self.client.post(reverse("register"), {
            "full_name": "Nasir Bello",
            "email": "nasir@example.com",
            "phone": "+2348012345678",
            "password": "StrongPass123!",
            "confirm_password": "StrongPass123!",
            "accepted_terms": "on",
        })
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(email="nasir@example.com")
        self.assertTrue(hasattr(user, "profile"))
        self.assertTrue(hasattr(user, "wallet"))

    def test_login(self):
        response = self.client.post(reverse("login"), {"username": "ada@example.com", "password": "StrongPass123!"})
        self.assertRedirects(response, reverse("dashboard"))

    def test_deposit_credits_wallet_and_transaction(self):
        simulate_deposit(self.user, Decimal("250000.00"))
        wallet = Wallet.objects.get(user=self.user)
        self.assertEqual(wallet.available_balance, Decimal("250000.00"))
        self.assertTrue(wallet.transactions.filter(type=WalletTransaction.Type.DEPOSIT).exists())

    def test_withdrawal_validates_balance(self):
        simulate_deposit(self.user, Decimal("10000.00"))
        simulate_withdrawal(self.user, Decimal("5000.00"), "Demo Bank", "0123456789", "Ada Demo")
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.available_balance, Decimal("5000.00"))
        with self.assertRaises(ValueError):
            simulate_withdrawal(self.user, Decimal("6000.00"), "Demo Bank", "0123456789", "Ada Demo")

    def test_market_buy_fills_and_updates_holding(self):
        simulate_deposit(self.user, Decimal("100000.00"))
        order = create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.MARKET, 100)
        self.assertEqual(order.status, Order.Status.FILLED)
        holding = Holding.objects.get(user=self.user, asset=self.asset)
        self.assertEqual(holding.quantity, 100)

    def test_insufficient_balance_rejects_buy_creation(self):
        with self.assertRaises(ValueError):
            create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.MARKET, 100)

    def test_limit_buy_reserves_then_fills_when_price_changes(self):
        simulate_deposit(self.user, Decimal("100000.00"))
        order = create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.LIMIT, 100, Decimal("500.00"))
        self.assertEqual(order.status, Order.Status.PENDING)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.reserved_balance, Decimal("50250.00"))
        self.asset.current_price = Decimal("495.00")
        self.asset.save()
        from trading.services import check_pending_orders
        check_pending_orders(self.asset)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.FILLED)

    def test_cancel_limit_order_releases_reserved_funds(self):
        simulate_deposit(self.user, Decimal("100000.00"))
        order = create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.LIMIT, 100, Decimal("500.00"))
        cancel_order(order.id, user=self.user)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.reserved_balance, Decimal("0.00"))
        self.assertEqual(self.user.wallet.available_balance, Decimal("100000.00"))

    def test_sell_requires_holdings_and_credits_proceeds(self):
        with self.assertRaises(ValueError):
            create_order(self.user, self.asset, Order.Side.SELL, Order.OrderType.MARKET, 1)
        simulate_deposit(self.user, Decimal("100000.00"))
        create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.MARKET, 100)
        sell = create_order(self.user, self.asset, Order.Side.SELL, Order.OrderType.MARKET, 50)
        self.assertEqual(sell.status, Order.Status.FILLED)
        self.assertEqual(Holding.objects.get(user=self.user, asset=self.asset).quantity, 50)

    def test_authorization_prevents_cancelling_another_users_order(self):
        simulate_deposit(self.user, Decimal("100000.00"))
        order = create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.LIMIT, 100, Decimal("500.00"))
        with self.assertRaises(Order.DoesNotExist):
            cancel_order(order.id, user=self.other)

    def test_portfolio_calculation(self):
        simulate_deposit(self.user, Decimal("100000.00"))
        create_order(self.user, self.asset, Order.Side.BUY, Order.OrderType.MARKET, 10)
        summary = portfolio_summary(self.user)
        self.assertEqual(summary["value"], Decimal("5250.00"))

# Create your tests here.
