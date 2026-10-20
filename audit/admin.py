from django.contrib import admin
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "event_type",
        "outcome",
        "actor",
        "document",
        "short_details",
    )
    list_filter = ("event_type", "outcome", "created_at")
    search_fields = ("details", "actor__username", "document__title")
    readonly_fields = (
        "created_at",
        "actor",
        "document",
        "event_type",
        "outcome",
        "details",
    )

    def short_details(self, obj):
        if obj.details and len(obj.details) > 60:
            return obj.details[:60] + "..."
        return obj.details
    short_details.short_description = "Details"

    # Disable add, change, and delete permissions in Django Admin
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
