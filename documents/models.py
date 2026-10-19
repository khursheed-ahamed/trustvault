from django.conf import settings
from django.db import models


class Document(models.Model):
    """A securely stored document with owner-based access control."""

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="secure_docs/%Y/%m/")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_documents",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self):
        return self.title

    def user_has_access(self, user) -> bool:
        """
        Server-side permission check.

        Access is granted if the user:
        1. Has the Admin role (full access), OR
        2. Is the document owner, OR
        3. Has an explicit DocumentPermission grant.
        """
        if not user.is_authenticated:
            return False
        if user.is_admin_role:
            return True
        if self.owner_id == user.pk:
            return True
        return self.permissions.filter(user=user).exists()


class DocumentPermission(models.Model):
    """Explicit grant of access from a document to a specific user."""

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_grants",
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="permissions_granted",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("document", "user")

    def __str__(self):
        return f"{self.user} → {self.document}"
