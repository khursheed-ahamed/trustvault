from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with role-based access control."""

    ADMIN = "ADMIN"
    OWNER = "OWNER"
    VIEWER = "VIEWER"

    ROLE_CHOICES = [
        (ADMIN, "Admin"),
        (OWNER, "Owner"),
        (VIEWER, "Viewer"),
    ]

    # Backward compatibility helper
    class Role:
        ADMIN = "ADMIN"
        OWNER = "OWNER"
        VIEWER = "VIEWER"

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=VIEWER,
    )

    def is_admin_role(self):
        """Return True if user has the ADMIN role."""
        return self.role == self.ADMIN

    def is_owner_role(self):
        """Return True if user has the OWNER role."""
        return self.role == self.OWNER

    def is_viewer_role(self):
        """Return True if user has the VIEWER role."""
        return self.role == self.VIEWER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

