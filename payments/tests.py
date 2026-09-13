import json
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse

from wallet.services import get_or_create_wallet

from .models import Payment
from .services import confirm_deposit, initiate_deposit


def _flw_response(status="successful", amount="5000.00", currency="NGN", tx_id="123456"):
    response = Mock()
    response.raise_for_status = Mock()
    response.json.return_value = {
        "status": "success",
        "data": {"status": status, "amount": amount, "currency": currency, "id": tx_id},
    }
    return response


@override_settings(PAYMENT_PROVIDER="flutterwave", FLW_SECRET_KEY="test-secret", FLW_SECRET_HASH="test-hash")
class FlutterwaveDepositTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="ada@example.com", email="ada@example.com", password="StrongPass123!")
        get_or_create_wallet(self.user)

    @patch("payments.providers.requests.post")
    def test_initiate_deposit_creates_pending_payment_without_crediting_wallet(self, mock_post):
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"status": "success", "data": {"link": "https://checkout.flutterwave.com/pay/abc"}}),
        )

        payment = initiate_deposit(self.user, Decimal("5000.00"), redirect_url="https://example.com/callback/")

        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.checkout_url, "https://checkout.flutterwave.com/pay/abc")
        self.assertIsNone(payment.credited_at)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.available_balance, Decimal("0.00"))

    @patch("payments.providers.requests.get")
    @patch("payments.providers.requests.post")
    def test_confirm_deposit_credits_wallet_on_verified_success(self, mock_post, mock_get):
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"status": "success", "data": {"link": "https://checkout.flutterwave.com/pay/abc"}}),
        )
        payment = initiate_deposit(self.user, Decimal("5000.00"))

        mock_get.return_value = _flw_response(status="successful", amount="5000.00")
        confirmed = confirm_deposit(payment.reference)

        self.assertEqual(confirmed.status, Payment.Status.SUCCESSFUL)
        self.assertIsNotNone(confirmed.credited_at)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.available_balance, Decimal("5000.00"))

    @patch("payments.providers.requests.get")
    @patch("payments.providers.requests.post")
    def test_confirm_deposit_is_idempotent(self, mock_post, mock_get):
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"status": "success", "data": {"link": "https://checkout.flutterwave.com/pay/abc"}}),
        )
        payment = initiate_deposit(self.user, Decimal("5000.00"))
        mock_get.return_value = _flw_response(status="successful", amount="5000.00")

        confirm_deposit(payment.reference)
        confirm_deposit(payment.reference)
        confirm_deposit(payment.reference)

        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.available_balance, Decimal("5000.00"))
        self.assertEqual(self.user.wallet.transactions.count(), 1)

    @patch("payments.providers.requests.get")
    @patch("payments.providers.requests.post")
    def test_confirm_deposit_rejects_underpaid_amount(self, mock_post, mock_get):
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"status": "success", "data": {"link": "https://checkout.flutterwave.com/pay/abc"}}),
        )
        payment = initiate_deposit(self.user, Decimal("5000.00"))
        # Attacker/glitch scenario: provider reports a lower amount than requested.
        mock_get.return_value = _flw_response(status="successful", amount="10.00")

        confirmed = confirm_deposit(payment.reference)

        self.assertEqual(confirmed.status, Payment.Status.FAILED)
        self.assertIsNone(confirmed.credited_at)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.available_balance, Decimal("0.00"))

    @patch("payments.providers.requests.get")
    @patch("payments.providers.requests.post")
    def test_webhook_rejects_missing_or_wrong_signature(self, mock_post, mock_get):
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"status": "success", "data": {"link": "https://checkout.flutterwave.com/pay/abc"}}),
        )
        payment = initiate_deposit(self.user, Decimal("5000.00"))
        body = json.dumps({"data": {"tx_ref": payment.reference}})

        response = self.client.post(reverse("payment_webhook"), data=body, content_type="application/json")
        self.assertEqual(response.status_code, 401)

        response = self.client.post(
            reverse("payment_webhook"), data=body, content_type="application/json", HTTP_VERIF_HASH="wrong-hash"
        )
        self.assertEqual(response.status_code, 401)
        mock_get.assert_not_called()

    @patch("payments.providers.requests.get")
    @patch("payments.providers.requests.post")
    def test_webhook_with_valid_signature_confirms_and_credits(self, mock_post, mock_get):
        mock_post.return_value = Mock(
            raise_for_status=Mock(),
            json=Mock(return_value={"status": "success", "data": {"link": "https://checkout.flutterwave.com/pay/abc"}}),
        )
        payment = initiate_deposit(self.user, Decimal("5000.00"))
        mock_get.return_value = _flw_response(status="successful", amount="5000.00")

        body = json.dumps({"data": {"tx_ref": payment.reference}})
        response = self.client.post(
            reverse("payment_webhook"), data=body, content_type="application/json", HTTP_VERIF_HASH="test-hash"
        )

        self.assertEqual(response.status_code, 200)
        self.user.wallet.refresh_from_db()
        self.assertEqual(self.user.wallet.available_balance, Decimal("5000.00"))
