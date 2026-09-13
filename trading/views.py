from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from investments.models import Asset
from portfolio.services import portfolio_summary

from .forms import OrderForm
from .models import Order
from .services import cancel_order, create_order, fee_for


@login_required
def order_ticket(request, symbol, side):
    asset = get_object_or_404(Asset, symbol=symbol, is_enabled=True)
    holding = request.user.holdings.filter(asset=asset).first()
    initial = {"side": side, "order_type": Order.OrderType.MARKET}
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            try:
                order = create_order(request.user, asset, **form.cleaned_data)
                if order.status == Order.Status.FILLED:
                    messages.success(request, "Demo order filled successfully.")
                else:
                    messages.success(request, "Demo limit order placed and pending.")
                return redirect("orders")
            except ValueError as exc:
                messages.error(request, str(exc))
    else:
        form = OrderForm(initial=initial)
    return render(
        request,
        "trading/ticket.html",
        {
            "asset": asset,
            "side": side,
            "form": form,
            "holding": holding,
            "fee_rate": "0.5%",
            "market_fee": fee_for(asset.current_price),
        },
    )


@login_required
def orders(request):
    user_orders = request.user.orders.select_related("asset")
    return render(
        request,
        "trading/orders.html",
        {
            "open_orders": user_orders.filter(status=Order.Status.PENDING),
            "history": user_orders.exclude(status=Order.Status.PENDING),
        },
    )


@login_required
def cancel(request, order_id):
    if request.method == "POST":
        try:
            cancel_order(order_id, user=request.user)
            messages.success(request, "Demo order cancelled and reserved funds released.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("orders")

# Create your views here.
