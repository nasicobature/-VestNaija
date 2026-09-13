from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from .models import Asset


@login_required
def marketplace(request):
    return render(request, "investments/marketplace.html", {"assets": Asset.objects.filter(is_enabled=True)})


@login_required
def asset_detail(request, symbol):
    asset = get_object_or_404(Asset, symbol=symbol, is_enabled=True)
    holding = request.user.holdings.filter(asset=asset).first()
    return render(request, "investments/detail.html", {"asset": asset, "holding": holding})

# Create your views here.
