from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Document(models.Model):
    """
    Secure Document model.
    Files are stored in secure_docs/ and never exposed via public URLs.
    """

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="secure_docs/%Y/%m/")
    original_filename = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, default="")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} (Owner: {self.owner.username})"

    def save(self, *args, **kwargs):
        # Automatically populate original_filename from uploaded file if not provided
        if not self.original_filename and self.file:
            self.original_filename = getattr(self.file, "name", "")
        super().save(*args, **kwargs)


class DocumentPermission(models.Model):
    """
    Explicit document access permission granted to a user.
    """

    READ = "READ"
    EDIT = "EDIT"
    PERMISSION_CHOICES = [
        (READ, "Read"),
        (EDIT, "Edit"),
    ]

    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_permissions",
    )
    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
    )
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="granted_document_permissions",
    )
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("document", "user")

    def __str__(self):
        status = "Active" if self.is_active else "Revoked"
        return f"{self.user.username} -> {self.document.title} [{self.permission}] ({status})"

    @property
    def is_active(self):
        """Return True only when revoked_at is None/empty."""
        return self.revoked_at is None

    def clean(self):
        """
        Validate that the document owner cannot grant permissions to themselves.
        """
        super().clean()
        if hasattr(self, "document") and hasattr(self, "user"):
            if self.document.owner_id == self.user_id:
                raise ValidationError(
                    "A document owner cannot be granted explicit permissions on their own document."
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
