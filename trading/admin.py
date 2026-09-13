from django.contrib import admin

from .models import FeeSchedule, Holding, Order, Trade, TradingSetting
from .services import cancel_order, try_execute_order


@admin.action(description="Execute selected pending orders")
def execute_demo_orders(modeladmin, request, queryset):
    for order in queryset:
        try_execute_order(order)


@admin.action(description="Cancel selected pending orders")
def cancel_demo_orders(modeladmin, request, queryset):
    for order in queryset:
        if order.status == Order.Status.PENDING:
            cancel_order(order.id)


@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ("user", "asset", "quantity", "average_price", "updated_at")
    search_fields = ("user__email", "asset__symbol")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "asset", "side", "order_type", "quantity", "limit_price", "status", "created_at")
    list_filter = ("side", "order_type", "status")
    search_fields = ("user__email", "asset__symbol")
    actions = [execute_demo_orders, cancel_demo_orders]


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("order", "user", "asset", "quantity", "price", "gross_amount", "fee", "created_at")
    search_fields = ("user__email", "asset__symbol")


@admin.register(FeeSchedule)
class FeeScheduleAdmin(admin.ModelAdmin):
    list_display = ("name", "rate", "is_active", "updated_at")
    list_filter = ("is_active",)


@admin.register(TradingSetting)
class TradingSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at")
    search_fields = ("key", "description")

# Register your models here.
