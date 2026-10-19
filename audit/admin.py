from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "resource_type", "resource_id")
    list_filter = ("action", "resource_type")
    search_fields = ("detail", "user__username")
    readonly_fields = (
        "user", "action", "resource_type", "resource_id",
        "detail", "timestamp", "ip_address",
    )

    def has_add_permission(self, request):
        return False  # Audit logs are created programmatically only

    def has_change_permission(self, request, obj=None):
        return False  # Audit logs are immutable

    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs must not be deleted
