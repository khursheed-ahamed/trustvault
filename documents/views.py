from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from audit.models import AuditEvent
from .forms import DocumentPermissionForm, DocumentUploadForm
from .models import Document, DocumentPermission
from .services import can_access_document, record_access_denied


@login_required
def document_dashboard(request):
    """
    List only documents where the logged-in user is either the owner
    or has an active (non-revoked) permission.
    """
    documents = Document.objects.filter(
        Q(owner=request.user) |
        Q(permissions__user=request.user, permissions__revoked_at__isnull=True)
    ).distinct()

    return render(
        request,
        "documents/dashboard.html",
        {"documents": documents},
    )


@login_required
def document_upload(request):
    """
    Upload a new secure document. Restricted strictly to users with role 'OWNER'.
    """
    if request.user.role != "OWNER":
        raise PermissionDenied("Only users with the 'OWNER' role can upload new documents.")

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.owner = request.user
            uploaded_file = form.cleaned_data["file"]
            document.original_filename = uploaded_file.name
            document.save()

            # Record audit event
            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                event_type=AuditEvent.UPLOAD,
                outcome=AuditEvent.SUCCESS,
                details=f"Document '{document.title}' uploaded successfully by owner '{request.user.username}'.",
            )

            messages.success(request, f"Document '{document.title}' uploaded successfully.")
            return redirect("secure_document_detail", document_id=document.pk)
    else:
        form = DocumentUploadForm()

    return render(request, "documents/document_upload.html", {"form": form})


@login_required
def secure_document_detail(request, document_id):
    """
    Protected document detail view.
    Checks server-side permission, records audit event, and renders metadata without file URLs.
    """
    document = get_object_or_404(Document, pk=document_id)

    # Server-side authorization check
    if not can_access_document(request.user, document, "read"):
        record_access_denied(request.user, document, "read")
        raise PermissionDenied("You do not have permission to view this document.")

    # Record successful VIEW audit event
    AuditEvent.objects.create(
        actor=request.user,
        document=document,
        event_type=AuditEvent.VIEW,
        outcome=AuditEvent.SUCCESS,
        details=f"User '{request.user.username}' viewed details of document '{document.title}'.",
    )

    is_owner = (document.owner_id == request.user.pk)
    return render(
        request,
        "documents/document_detail.html",
        {
            "document": document,
            "is_owner": is_owner,
        },
    )


@login_required
def secure_document_download(request, document_id):
    """
    Protected document download view.
    Streams file bytes through FileResponse; never exposes public URLs.
    """
    document = get_object_or_404(Document, pk=document_id)

    # Server-side authorization check
    if not can_access_document(request.user, document, "read"):
        record_access_denied(request.user, document, "download")
        raise PermissionDenied("You do not have permission to download this document.")

    # Record successful DOWNLOAD audit event
    AuditEvent.objects.create(
        actor=request.user,
        document=document,
        event_type=AuditEvent.DOWNLOAD,
        outcome=AuditEvent.SUCCESS,
        details=f"User '{request.user.username}' downloaded file '{document.original_filename}'.",
    )

    # Stream file bytes safely via FileResponse in binary mode with application/pdf MIME type
    return FileResponse(
        document.file.open("rb"),
        as_attachment=True,
        filename=document.original_filename,
        content_type="application/pdf",
    )


@login_required
def manage_document_permissions(request, document_id):
    """
    Manage user permissions for a document. Restricted strictly to the document owner.
    """
    document = get_object_or_404(Document, pk=document_id)

    # Only document owner may manage permissions
    if document.owner_id != request.user.pk:
        record_access_denied(request.user, document, "manage_permissions")
        raise PermissionDenied("Only the document owner may manage permissions.")

    if request.method == "POST":
        form = DocumentPermissionForm(
            request.POST,
            document=document,
            current_user=request.user,
        )
        if form.is_valid():
            target_user = form.cleaned_data["user"]
            perm_level = form.cleaned_data["permission"]

            perm, created = DocumentPermission.objects.get_or_create(
                document=document,
                user=target_user,
                defaults={
                    "permission": perm_level,
                    "granted_by": request.user,
                    "revoked_at": None,
                },
            )

            # If permission already existed, update it and reactivate if revoked
            if not created:
                perm.permission = perm_level
                perm.granted_by = request.user
                perm.revoked_at = None
                perm.save()

            # Record audit event
            AuditEvent.objects.create(
                actor=request.user,
                document=document,
                event_type=AuditEvent.PERMISSION_GRANTED,
                outcome=AuditEvent.SUCCESS,
                details=f"Owner '{request.user.username}' granted '{perm_level}' permission to '{target_user.username}'.",
            )

            action_text = "granted" if created else "updated"
            messages.success(
                request,
                f"Successfully {action_text} {perm_level} access to {target_user.username}."
            )
            return redirect("manage_document_permissions", document_id=document.pk)
    else:
        form = DocumentPermissionForm(document=document, current_user=request.user)

    permissions = document.permissions.select_related("user", "granted_by").order_by("-granted_at")
    return render(
        request,
        "documents/manage_permissions.html",
        {
            "document": document,
            "form": form,
            "permissions": permissions,
        },
    )


@login_required
@require_POST
def revoke_document_permission(request, document_id, permission_id):
    """
    Revoke an active document permission. Restricted strictly to the document owner.
    """
    document = get_object_or_404(Document, pk=document_id)

    # Only document owner may revoke permissions
    if document.owner_id != request.user.pk:
        record_access_denied(request.user, document, "manage_permissions")
        raise PermissionDenied("Only the document owner may revoke permissions.")

    permission = get_object_or_404(DocumentPermission, pk=permission_id, document=document)
    permission.revoked_at = timezone.now()
    permission.save()

    # Record audit event
    AuditEvent.objects.create(
        actor=request.user,
        document=document,
        event_type=AuditEvent.PERMISSION_REVOKED,
        outcome=AuditEvent.SUCCESS,
        details=f"Owner '{request.user.username}' revoked access for '{permission.user.username}'.",
    )

    messages.success(
        request,
        f"Permission for user '{permission.user.username}' has been revoked immediately."
    )
    return redirect("manage_document_permissions", document_id=document.pk)
