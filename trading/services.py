from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from audit.services import log_audit
from wallet.models import WalletTransaction
from wallet.services import consume_reserved, credit_wallet, release_reserved, reserve_funds

from .models import Holding, Order, Trade


def fee_for(amount):
    return (Decimal(amount) * Decimal(settings.DEFAULT_BROKER_FEE_RATE)).quantize(Decimal("0.01"))


@transaction.atomic
def create_order(user, asset, side, order_type, quantity, limit_price=None):
    quantity = int(quantity)
    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero.")
    if order_type == Order.OrderType.LIMIT and not limit_price:
        raise ValueError("Limit price is required for limit orders.")

    price_basis = Decimal(limit_price) if limit_price else asset.current_price
    gross = price_basis * quantity
    fee = fee_for(gross)

    if side == Order.Side.BUY:
        reserve_funds(user, gross + fee, f"Reserved for {asset.symbol} buy order")
        reserved = gross + fee
    else:
        holding = Holding.objects.filter(user=user, asset=asset).first()
        if not holding or holding.quantity < quantity:
            raise ValueError("Insufficient holdings for sell order.")
        reserved = Decimal("0.00")

    order = Order.objects.create(
        user=user,
        asset=asset,
        side=side,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit_price,
        estimated_fee=fee,
        reserved_amount=reserved,
    )
    log_audit(user, "demo_order_created", order, {"side": side, "order_type": order_type, "quantity": quantity})
    return try_execute_order(order)


@transaction.atomic
def try_execute_order(order):
    order = Order.objects.select_for_update().select_related("asset", "user").get(pk=order.pk)
    if order.status != Order.Status.PENDING:
        return order
    current_price = order.asset.current_price
    should_fill = order.order_type == Order.OrderType.MARKET
    if order.order_type == Order.OrderType.LIMIT and order.side == Order.Side.BUY:
        should_fill = current_price <= order.limit_price
    if order.order_type == Order.OrderType.LIMIT and order.side == Order.Side.SELL:
        should_fill = current_price >= order.limit_price
    if not should_fill:
        return order

    gross = current_price * order.quantity
    fee = fee_for(gross)
    holding, _ = Holding.objects.select_for_update().get_or_create(user=order.user, asset=order.asset)

    if order.side == Order.Side.BUY:
        consume_reserved(order.user, min(order.reserved_amount, gross + fee))
        if order.reserved_amount > gross + fee:
            release_reserved(order.user, order.reserved_amount - gross - fee, f"Refund for {order.asset.symbol} order")
        new_total_cost = (holding.average_price * holding.quantity) + gross
        holding.quantity += order.quantity
        holding.average_price = new_total_cost / holding.quantity
        holding.save(update_fields=["quantity", "average_price", "updated_at"])
    else:
        if holding.quantity < order.quantity:
            order.status = Order.Status.REJECTED
            order.save(update_fields=["status"])
            return order
        holding.quantity -= order.quantity
        holding.save(update_fields=["quantity", "updated_at"])
        credit_wallet(order.user, gross - fee, WalletTransaction.Type.SALE_PROCEEDS, f"Demo sale proceeds for {order.asset.symbol}")

    Trade.objects.create(
        order=order,
        user=order.user,
        asset=order.asset,
        quantity=order.quantity,
        price=current_price,
        gross_amount=gross,
        fee=fee,
    )
    order.filled_quantity = order.quantity
    order.execution_price = current_price
    order.estimated_fee = fee
    order.status = Order.Status.FILLED
    order.executed_at = timezone.now()
    order.save(update_fields=["filled_quantity", "execution_price", "estimated_fee", "status", "executed_at"])
    log_audit(order.user, "demo_order_filled", order, {"price": str(current_price), "quantity": order.quantity})
    return order


@transaction.atomic
def cancel_order(order_id, user=None):
    qs = Order.objects.select_for_update()
    if user is not None:
        qs = qs.filter(user=user)
    order = qs.get(pk=order_id)
    if order.status != Order.Status.PENDING:
        raise ValueError("Only pending orders can be cancelled.")
    if order.side == Order.Side.BUY and order.reserved_amount:
        release_reserved(order.user, order.reserved_amount, f"Cancelled {order.asset.symbol} buy order")
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    log_audit(order.user, "demo_order_cancelled", order, {"reserved_released": str(order.reserved_amount)})
    return order


def check_pending_orders(asset):
    for order in Order.objects.filter(asset=asset, status=Order.Status.PENDING).order_by("created_at"):
        try_execute_order(order)
