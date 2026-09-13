from django.contrib import admin

from .models import Wallet, WalletTransaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ("user", "available_balance", "reserved_balance", "total_deposited", "total_withdrawn")
    search_fields = ("user__email",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "wallet", "type", "amount", "status", "created_at")
    list_filter = ("type", "status")
    search_fields = ("wallet__user__email", "reference", "description")
    readonly_fields = ("id", "created_at")

# Register your models here.
