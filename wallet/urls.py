from django.urls import path

from . import views

urlpatterns = [
    path("", views.wallet_home, name="wallet"),
    path("deposit/", views.deposit, name="deposit"),
    path("withdraw/", views.withdraw, name="withdraw"),
    path("transactions/", views.transactions, name="transactions"),
]
