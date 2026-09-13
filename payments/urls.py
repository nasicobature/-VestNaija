from django.urls import path

from . import views

urlpatterns = [
    path("webhook/", views.flutterwave_webhook, name="payment_webhook"),
    path("callback/", views.deposit_callback, name="deposit_callback"),
]
