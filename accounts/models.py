from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user with a role field for access control."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OWNER = "owner", "Owner"
        VIEWER = "viewer", "Viewer"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER,
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
