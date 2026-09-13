from django.db import transaction
from django.utils import timezone

from audit.services import log_audit
from wallet.models import WalletTransaction
from wallet.services import credit_wallet, request_withdrawal

from .models import Deposit, Withdrawal
from .providers import MockPaymentProvider


@transaction.atomic
def simulate_deposit(user, amount):
    provider = MockPaymentProvider()
    payment = provider.initialize_payment(user, amount)
    payment = provider.verify_payment(payment.reference)
    Deposit.objects.create(user=user, payment=payment, amount=amount, status=payment.status)
    credit_wallet(user, amount, WalletTransaction.Type.DEPOSIT, "Demo wallet deposit", str(payment.reference))
    payment.credited_at = timezone.now()
    payment.save(update_fields=["credited_at"])
    log_audit(user, "demo_deposit_completed", payment, {"amount": str(amount)})
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
    request_withdrawal(user, amount, "Demo withdrawal request", str(withdrawal.id))
    log_audit(user, "demo_withdrawal_requested", withdrawal, {"amount": str(amount), "bank": bank})
    return withdrawal
