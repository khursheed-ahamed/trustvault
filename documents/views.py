import mimetypes

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from audit.models import AuditEvent
from .models import Document, DocumentPermission


@login_required
def dashboard(request):
    """Show documents the current user may access."""
    user = request.user
    is_admin = user.is_admin_role() if callable(getattr(user, "is_admin_role", None)) else getattr(user, "is_admin_role", False)
    if is_admin:
        documents = Document.objects.all()
    else:
        documents = Document.objects.filter(
            Q(owner=user) | Q(permissions__user=user)
        ).distinct()
    return render(request, "documents/dashboard.html", {"documents": documents})


@login_required
def upload_document(request):
    """Upload a new document (owner is the logged-in user)."""
    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        uploaded_file = request.FILES.get("file")
        if title and uploaded_file:
            doc = Document.objects.create(
                title=title,
                file=uploaded_file,
                owner=request.user,
                description=request.POST.get("description", ""),
            )
            AuditEvent.objects.create(
                user=request.user,
                action="upload",
                resource_type="Document",
                resource_id=doc.pk,
                detail=f"Uploaded '{doc.title}'",
            )
            return redirect("home")
    return render(request, "documents/upload.html")


@login_required
def download_document(request, pk):
    """
    Serve a document file ONLY after a server-side permission check.

    Files are never served via a public URL — they always pass through this
    view which enforces access control.
    """
    document = get_object_or_404(Document, pk=pk)

    if not document.user_has_access(request.user):
        AuditEvent.objects.create(
            user=request.user,
            action="download_denied",
            resource_type="Document",
            resource_id=document.pk,
            detail=f"Access denied to '{document.title}'",
        )
        raise PermissionDenied("You do not have permission to access this document.")

    AuditEvent.objects.create(
        user=request.user,
        action="download",
        resource_type="Document",
        resource_id=document.pk,
        detail=f"Downloaded '{document.title}'",
    )

    content_type, _ = mimetypes.guess_type(document.file.name)
    response = FileResponse(
        document.file.open("rb"),
        content_type=content_type or "application/octet-stream",
    )
    response["Content-Disposition"] = f'attachment; filename="{document.title}"'
    return response


@login_required
def grant_access(request, pk):
    """Let an owner or admin grant access to another user."""
    document = get_object_or_404(Document, pk=pk)
    user = request.user

    # Only the owner or an admin can grant access
    is_admin = user.is_admin_role() if callable(getattr(user, "is_admin_role", None)) else getattr(user, "is_admin_role", False)
    if document.owner != user and not is_admin:
        raise PermissionDenied

    if request.method == "POST":
        from accounts.models import User

        username = request.POST.get("username", "").strip()
        try:
            target_user = User.objects.get(username=username)
        except User.DoesNotExist:
            return render(
                request,
                "documents/grant_access.html",
                {"document": document, "error": "User not found."},
            )

        DocumentPermission.objects.get_or_create(
            document=document,
            user=target_user,
            defaults={"granted_by": user},
        )
        AuditEvent.objects.create(
            user=user,
            action="grant_access",
            resource_type="Document",
            resource_id=document.pk,
            detail=f"Granted access to '{target_user.username}'",
        )
        return redirect("home")

    return render(request, "documents/grant_access.html", {"document": document})
