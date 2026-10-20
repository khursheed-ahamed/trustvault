from audit.models import AuditEvent


def can_access_document(user, document, action):
    """
    Central server-side authorization check for document operations.

    Supported actions:
    - "read"
    - "edit"
    - "delete"
    - "manage_permissions"

    Rules:
    - Unauthenticated users always return False.
    - The document owner can perform all actions.
    - A named user with an active EDIT permission can "read" and "edit",
      but cannot "delete" or "manage_permissions".
    - A named user with an active READ permission can only "read".
    - Everyone else returns False.
    - Staff / superuser / administrator status alone does NOT grant access.
      Document access must be explicit, except for the owner.
    """
    valid_actions = ("read", "edit", "delete", "manage_permissions")
    if action not in valid_actions:
        return False

    if not user or not user.is_authenticated:
        return False

    # The document owner can perform every action
    if document.owner_id == user.pk:
        return True

    # Look for an active explicit permission (revoked_at is empty/null)
    active_permission = document.permissions.filter(
        user=user,
        revoked_at__isnull=True,
    ).first()

    if active_permission:
        if active_permission.permission == "EDIT":
            return action in ("read", "edit")
        elif active_permission.permission == "READ":
            return action == "read"

    return False


def record_access_denied(user, document, action):
    """
    Create an AuditEvent entry when access is denied to a user.
    """
    actor = user if (user and user.is_authenticated) else None
    username = user.username if actor else "Anonymous"
    doc_title = document.title if document else "Unknown"
    doc_id = document.pk if document else "None"

    return AuditEvent.objects.create(
        actor=actor,
        document=document,
        event_type=AuditEvent.ACCESS_DENIED,
        outcome=AuditEvent.DENIED,
        details=(
            f"User '{username}' was denied '{action}' access "
            f"on document '{doc_title}' (ID: {doc_id})."
        ),
    )
