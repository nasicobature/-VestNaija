from django.db import transaction
from django.utils import timezone

from audit.services import log_audit
from wallet.models import WalletTransaction
from wallet.services import credit_wallet, request_withdrawal

from .models import Deposit, Payment, Withdrawal
from .providers import MockPaymentProvider, get_payment_provider


@transaction.atomic
def simulate_deposit(user, amount):
    provider = MockPaymentProvider()
    payment = provider.initialize_payment(user, amount)
    payment = provider.verify_payment(payment.reference)
    Deposit.objects.create(user=user, payment=payment, amount=amount, status=payment.status)
    credit_wallet(user, amount, WalletTransaction.Type.DEPOSIT, "Sandbox wallet deposit", str(payment.reference))
    payment.credited_at = timezone.now()
    payment.save(update_fields=["credited_at"])
    log_audit(user, "mock_deposit_completed", payment, {"amount": str(amount)})
    return payment


@transaction.atomic
def initiate_deposit(user, amount, redirect_url=None):
    """Start a real deposit through the configured provider (e.g. Flutterwave).

    The wallet is NOT credited here. Crediting only happens once
    confirm_deposit() has re-verified the payment against the provider's
    API, via the webhook or the checkout redirect callback.
    """
    provider = get_payment_provider()
    payment = provider.initialize_payment(user, amount, redirect_url=redirect_url)
    Deposit.objects.create(user=user, payment=payment, amount=amount, status=payment.status)
    log_audit(user, "deposit_initiated", payment, {"amount": str(amount), "provider": payment.provider})
    return payment


@transaction.atomic
def confirm_deposit(reference):
    """Re-verify a payment against the provider and credit the wallet exactly once.

    Safe to call repeatedly (webhook retries, plus the checkout redirect
    landing on the same payment) because it checks credited_at under a row
    lock before crediting.
    """
    payment = Payment.objects.select_for_update().get(reference=reference)
    if payment.credited_at:
        return payment

    provider = get_payment_provider()
    payment = provider.verify_payment(reference)

    deposit = getattr(payment, "deposit", None)
    if deposit is not None and deposit.status != payment.status:
        deposit.status = payment.status
        deposit.save(update_fields=["status"])

    if payment.status == Payment.Status.SUCCESSFUL and not payment.credited_at:
        credit_wallet(payment.user, payment.amount, WalletTransaction.Type.DEPOSIT, "Wallet deposit", str(payment.reference))
        payment.credited_at = timezone.now()
        payment.save(update_fields=["credited_at"])
        log_audit(payment.user, "deposit_confirmed", payment, {"amount": str(payment.amount)})
    elif payment.status == Payment.Status.FAILED:
        log_audit(payment.user, "deposit_failed", payment, {"amount": str(payment.amount)})

    return payment


@transaction.atomic
def simulate_withdrawal(user, amount, bank, account_number, account_name):
    withdrawal = Withdrawal.objects.create(
        user=user,
        amount=amount,
        bank=bank,
        account_number=account_number,
        account_name=account_name,
        status=Withdrawal.Status.PENDING,
    )
    request_withdrawal(user, amount, "Withdrawal request", str(withdrawal.id))
    log_audit(user, "withdrawal_requested", withdrawal, {"amount": str(amount), "bank": bank})
    return withdrawal
