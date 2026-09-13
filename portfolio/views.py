from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .services import portfolio_summary


@login_required
def portfolio(request):
    return render(request, "portfolio/home.html", {"summary": portfolio_summary(request.user)})

# Create your views here.
