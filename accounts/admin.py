from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "account_status", "kyc_status", "created_at")
    list_filter = ("kyc_status", "account_status")
    search_fields = ("user__email", "user__first_name", "user__last_name", "phone")

# Register your models here.
