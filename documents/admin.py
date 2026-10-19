from django.contrib import admin

from .models import Document, DocumentPermission


class PermissionInline(admin.TabularInline):
    model = DocumentPermission
    extra = 1
    raw_id_fields = ("user", "granted_by")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "uploaded_at")
    list_filter = ("owner",)
    inlines = [PermissionInline]


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = ("document", "user", "granted_by", "granted_at")
