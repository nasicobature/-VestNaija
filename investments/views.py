from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Asset


@login_required
def marketplace(request):
    assets = Asset.objects.filter(is_enabled=True)

    query = request.GET.get("q", "").strip()
    if query:
        assets = assets.filter(Q(symbol__icontains=query) | Q(name__icontains=query))

    sector = request.GET.get("sector", "").strip()
    if sector:
        assets = assets.filter(sector=sector)

    return render(
        request,
        "investments/marketplace.html",
        {
            "assets": assets,
            "sectors": Asset.Sector.choices,
            "selected_sector": sector,
            "query": query,
        },
    )


@login_required
def asset_detail(request, symbol):
    asset = get_object_or_404(Asset, symbol=symbol, is_enabled=True)
    holding = request.user.holdings.filter(asset=asset).first()
    return render(request, "investments/detail.html", {"asset": asset, "holding": holding})
