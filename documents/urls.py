from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("upload/", views.upload_document, name="upload"),
    path("<int:pk>/download/", views.download_document, name="download"),
    path("<int:pk>/grant/", views.grant_access, name="grant_access"),
]
