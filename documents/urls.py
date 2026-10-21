from django.urls import path
from . import views

urlpatterns = [
    path("", views.document_dashboard, name="document_dashboard"),
    path("upload/", views.document_upload, name="document_upload"),
    path("<int:document_id>/", views.secure_document_detail, name="secure_document_detail"),
    path("<int:document_id>/download/", views.secure_document_download, name="secure_document_download"),
    path("<int:document_id>/permissions/", views.manage_document_permissions, name="manage_document_permissions"),
    path("<int:document_id>/permissions/<int:permission_id>/revoke/", views.revoke_document_permission, name="revoke_document_permission"),
]
