from django.urls import path

from . import views

urlpatterns = [
    path("", views.marketplace, name="marketplace"),
    path("<str:symbol>/", views.asset_detail, name="asset_detail"),
]
