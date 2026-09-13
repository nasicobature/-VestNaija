def portfolio_summary(user):
    holdings = user.holdings.select_related("asset").all()
    value = sum(h.quantity * h.asset.current_price for h in holdings)
    cost = sum(h.quantity * h.average_price for h in holdings)
    total_return = value - cost
    return {
        "holdings": holdings,
        "value": value,
        "cost": cost,
        "total_return": total_return,
        "today_change": sum(h.quantity * h.asset.price_change for h in holdings),
    }
