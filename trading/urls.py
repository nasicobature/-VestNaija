from django.urls import path

from . import views

urlpatterns = [
    path("", views.orders, name="orders"),
    path("<uuid:order_id>/cancel/", views.cancel, name="cancel_order"),
    path("<str:symbol>/<str:side>/", views.order_ticket, name="order_ticket"),
]
