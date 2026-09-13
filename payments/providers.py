from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

from .models import Payment


class PaymentProvider:
    def initialize_payment(self, user, amount, redirect_url=None):
        raise NotImplementedError

    def verify_payment(self, reference):
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    def initialize_payment(self, user, amount, redirect_url=None):
        return Payment.objects.create(
            user=user,
            amount=amount,
            provider="mock",
            status=Payment.Status.PENDING,
            metadata={"mode": "mock", "message": "No real money is collected."},
        )

    def verify_payment(self, reference):
        payment = Payment.objects.get(reference=reference)
        payment.status = Payment.Status.SUCCESSFUL
        payment.verified_at = timezone.now()
        payment.save(update_fields=["status", "verified_at"])
        return payment


class FlutterwavePaymentProvider(PaymentProvider):
    """Real Flutterwave Standard (redirect) payment integration.

    Requires FLW_SECRET_KEY and FLW_BASE_URL to be set (via .env). Amounts
    are always re-verified against Flutterwave's API server-to-server before
    a wallet is credited; the webhook/redirect payload alone is never
    trusted for the amount or status.
    """

    def __init__(self):
        self.base_url = settings.FLW_BASE_URL.rstrip("/")
        self.secret_key = settings.FLW_SECRET_KEY
        if not self.secret_key:
            raise RuntimeError("FLW_SECRET_KEY is not configured. Set it in .env before using the Flutterwave provider.")

    def _headers(self):
        return {"Authorization": f"Bearer {self.secret_key}", "Content-Type": "application/json"}

    def initialize_payment(self, user, amount, redirect_url=None):
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            provider="flutterwave",
            status=Payment.Status.PENDING,
        )
        payload = {
            "tx_ref": payment.reference,
            "amount": str(amount),
            "currency": "NGN",
            "redirect_url": redirect_url or "",
            "customer": {
                "email": user.email,
                "name": user.get_full_name() or user.email,
            },
            "customizations": {"title": "VestNaija Wallet Funding"},
        }
        try:
            response = requests.post(f"{self.base_url}/payments", json=payload, headers=self._headers(), timeout=15)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            payment.status = Payment.Status.FAILED
            payment.metadata = {"error": str(exc)}
            payment.save(update_fields=["status", "metadata"])
            raise

        checkout_url = data.get("data", {}).get("link", "")
        payment.checkout_url = checkout_url
        payment.metadata = {"init_response_status": data.get("status", "")}
        payment.save(update_fields=["checkout_url", "metadata"])
        return payment

    def verify_payment(self, reference):
        payment = Payment.objects.get(reference=reference)
        response = requests.get(
            f"{self.base_url}/transactions/verify_by_reference",
            params={"tx_ref": reference},
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json().get("data", {})

        flw_status = data.get("status")
        currency = data.get("currency")
        try:
            amount_paid = Decimal(str(data.get("amount", "0")))
        except Exception:
            amount_paid = Decimal("0")

        if flw_status == "successful" and currency == "NGN" and amount_paid >= payment.amount:
            payment.status = Payment.Status.SUCCESSFUL
            payment.provider_transaction_id = str(data.get("id", "")) or None
        else:
            payment.status = Payment.Status.FAILED

        payment.verified_at = timezone.now()
        payment.save(update_fields=["status", "provider_transaction_id", "verified_at"])
        return payment


# Legacy names kept as aliases so other code referencing the original
# stub-provider interface keeps working.
OfficialPaymentProvider = FlutterwavePaymentProvider


def get_payment_provider():
    provider_name = (settings.PAYMENT_PROVIDER or "mock").lower()
    if provider_name.startswith("flutterwave"):
        return FlutterwavePaymentProvider()
    return MockPaymentProvider()
