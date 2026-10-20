from django.urls import path
from . import views

app_name = "documents"

urlpatterns = [
    path("<int:document_id>/", views.secure_document_detail, name="secure_document_detail"),
]
