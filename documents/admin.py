from django.contrib import admin
from .models import Document, DocumentPermission


class DocumentPermissionInline(admin.TabularInline):
    model = DocumentPermission
    extra = 0
    fields = ("user", "permission", "granted_by", "granted_at", "revoked_at")
    readonly_fields = ("granted_at",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "owner",
        "category",
        "original_filename",
        "created_at",
        "updated_at",
    )
    list_filter = ("category", "created_at", "owner")
    search_fields = ("title", "original_filename", "owner__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [DocumentPermissionInline]


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "user",
        "permission",
        "is_active",
        "granted_by",
        "granted_at",
        "revoked_at",
    )
    list_filter = ("permission", "granted_at", "revoked_at")
    search_fields = ("document__title", "user__username", "granted_by__username")
    readonly_fields = ("granted_at",)
