from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("action", "actor", "object_type", "object_id", "created_at")
    list_filter = ("action", "object_type")
    search_fields = ("actor__email", "object_id", "action")
    readonly_fields = ("created_at",)

# Register your models here.
