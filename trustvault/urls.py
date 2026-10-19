"""trustvault URL Configuration."""
from django.contrib import admin
from django.urls import include, path

from documents.views import dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("documents/", include("documents.urls")),
    path("", dashboard, name="home"),
]
