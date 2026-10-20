from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from .models import Document
from .services import can_access_document, record_access_denied


def secure_document_detail(request, document_id):
    """
    Minimal protected document detail view.
    Enforces server-side authorization before returning document information.
    """
    document = get_object_or_404(Document, pk=document_id)

    # Server-side authorization check
    if not can_access_document(request.user, document, "read"):
        record_access_denied(request.user, document, "read")
        raise PermissionDenied("You do not have permission to access this document.")

    # Return only the document title as plain text (no file bytes served)
    return HttpResponse(document.title)
