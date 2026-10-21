"""trustvault URL Configuration."""
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("accounts/", include("accounts.urls")),
    path("documents/", include("documents.urls")),
    path("", lambda request: redirect("document_dashboard"), name="home"),
]
