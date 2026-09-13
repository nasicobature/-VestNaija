from django.contrib import admin

from .models import Deposit, Payment, Withdrawal


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "status", "provider", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("reference", "user__email")


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email",)


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "bank", "account_number", "status", "created_at")
    list_filter = ("status", "bank")
    search_fields = ("user__email", "account_name", "account_number")

# Register your models here.
