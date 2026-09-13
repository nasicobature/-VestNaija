from django.utils import timezone

from .models import Payment


class PaymentProvider:
    def initialize_payment(self, user, amount):
        raise NotImplementedError

    def verify_payment(self, reference):
        raise NotImplementedError


class MockPaymentProvider(PaymentProvider):
    def initialize_payment(self, user, amount):
        return Payment.objects.create(
            user=user,
            amount=amount,
            status=Payment.Status.PENDING,
            metadata={"mode": "demo", "message": "No real money is collected."},
        )

    def verify_payment(self, reference):
        payment = Payment.objects.get(reference=reference)
        payment.status = Payment.Status.SUCCESSFUL
        payment.verified_at = timezone.now()
        payment.save(update_fields=["status", "verified_at"])
        return payment


class OfficialPaymentProvider(PaymentProvider):
    def initialize_payment(self, user, amount):
        raise NotImplementedError("Official payment integration requires licensed provider documentation and credentials.")

    def verify_payment(self, reference):
        raise NotImplementedError("Official payment verification is not available in demo mode.")
