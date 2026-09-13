from decimal import Decimal

from django.db import transaction

from .models import Wallet, WalletTransaction


def get_or_create_wallet(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    return wallet


@transaction.atomic
def credit_wallet(user, amount, tx_type, description, reference=""):
    amount = Decimal(amount)
    wallet = Wallet.objects.select_for_update().get(user=user)
    wallet.available_balance += amount
    if tx_type == WalletTransaction.Type.DEPOSIT:
        wallet.total_deposited += amount
    wallet.save(update_fields=["available_balance", "total_deposited", "updated_at"])
    return WalletTransaction.objects.create(
        wallet=wallet,
        amount=amount,
        type=tx_type,
        status=WalletTransaction.Status.COMPLETED,
        description=description,
        reference=reference,
    )


@transaction.atomic
def reserve_funds(user, amount, description, reference=""):
    amount = Decimal(amount)
    wallet = Wallet.objects.select_for_update().get(user=user)
    if wallet.available_balance < amount:
        raise ValueError("Insufficient available balance.")
    wallet.available_balance -= amount
    wallet.reserved_balance += amount
    wallet.save(update_fields=["available_balance", "reserved_balance", "updated_at"])
    return WalletTransaction.objects.create(
        wallet=wallet,
        amount=-amount,
        type=WalletTransaction.Type.BUY_RESERVATION,
        status=WalletTransaction.Status.COMPLETED,
        description=description,
        reference=reference,
    )


@transaction.atomic
def release_reserved(user, amount, description, reference=""):
    amount = Decimal(amount)
    wallet = Wallet.objects.select_for_update().get(user=user)
    release = min(wallet.reserved_balance, amount)
    wallet.reserved_balance -= release
    wallet.available_balance += release
    wallet.save(update_fields=["available_balance", "reserved_balance", "updated_at"])
    return WalletTransaction.objects.create(
        wallet=wallet,
        amount=release,
        type=WalletTransaction.Type.BUY_REFUND,
        status=WalletTransaction.Status.COMPLETED,
        description=description,
        reference=reference,
    )


@transaction.atomic
def consume_reserved(user, amount):
    amount = Decimal(amount)
    wallet = Wallet.objects.select_for_update().get(user=user)
    if wallet.reserved_balance < amount:
        raise ValueError("Reserved balance is lower than required.")
    wallet.reserved_balance -= amount
    wallet.save(update_fields=["reserved_balance", "updated_at"])
    return wallet


@transaction.atomic
def request_withdrawal(user, amount, description, reference=""):
    amount = Decimal(amount)
    wallet = Wallet.objects.select_for_update().get(user=user)
    if wallet.available_balance < amount:
        raise ValueError("Insufficient available balance.")
    wallet.available_balance -= amount
    wallet.total_withdrawn += amount
    wallet.save(update_fields=["available_balance", "total_withdrawn", "updated_at"])
    return WalletTransaction.objects.create(
        wallet=wallet,
        amount=-amount,
        type=WalletTransaction.Type.WITHDRAWAL,
        status=WalletTransaction.Status.PENDING,
        description=description,
        reference=reference,
    )
