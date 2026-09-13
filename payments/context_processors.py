from django.conf import settings


def payment_mode(request):
    return {"payments_live": (settings.PAYMENT_PROVIDER or "mock").lower().startswith("flutterwave")}
