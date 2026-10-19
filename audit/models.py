from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    """Immutable log entry for security-relevant actions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(
        max_length=50,
        help_text="e.g. login, upload, download, download_denied, grant_access",
    )
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.PositiveIntegerField(null=True, blank=True)
    detail = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.action} by {self.user}"
