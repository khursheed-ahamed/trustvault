"""trustvault URL Configuration."""
from django.contrib import admin
from django.urls import include, path

from audit.views import admin_audit_dashboard
from documents.views import document_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("activity/", admin_audit_dashboard, name="admin_audit_dashboard"),
    path("", include("accounts.urls")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("documents/", include("documents.urls")),
    path("", document_dashboard, name="home"),
]
