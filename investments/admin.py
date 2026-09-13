from django.contrib import admin

from trading.services import check_pending_orders

from .models import Asset, IPO


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "name", "market", "current_price", "status", "is_enabled", "is_demo_data")
    list_filter = ("market", "status", "is_enabled", "is_demo_data")
    search_fields = ("symbol", "name")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if "current_price" in form.changed_data:
            check_pending_orders(obj)


@admin.register(IPO)
class IPOAdmin(admin.ModelAdmin):
    list_display = ("asset", "offer_price", "minimum_subscription", "status")
    search_fields = ("asset__symbol", "asset__name")

# Register your models here.
