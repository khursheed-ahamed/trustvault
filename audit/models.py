from django.conf import settings
from django.db import models


class ImmutableAuditEventQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise TypeError("Audit events cannot be updated.")

    def delete(self):
        raise TypeError("Audit events cannot be deleted.")

    def bulk_update(self, objs, fields, batch_size=None):
        raise TypeError("Audit events cannot be updated.")


class AuditEventManager(models.Manager.from_queryset(ImmutableAuditEventQuerySet)):
    pass


class AuditEvent(models.Model):
    """
    Immutable audit log model recording all critical security and document events.
    """

    # Event types
    UPLOAD = "UPLOAD"
    VIEW = "VIEW"
    DOWNLOAD = "DOWNLOAD"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    PERMISSION_GRANTED = "PERMISSION_GRANTED"
    PERMISSION_REVOKED = "PERMISSION_REVOKED"
    ACCESS_DENIED = "ACCESS_DENIED"

    EVENT_TYPE_CHOICES = [
        (UPLOAD, "Upload"),
        (VIEW, "View"),
        (DOWNLOAD, "Download"),
        (UPDATE, "Update"),
        (DELETE, "Delete"),
        (PERMISSION_GRANTED, "Permission Granted"),
        (PERMISSION_REVOKED, "Permission Revoked"),
        (ACCESS_DENIED, "Access Denied"),
    ]

    # Outcomes
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    FAILURE = "FAILURE"

    OUTCOME_CHOICES = [
        (SUCCESS, "Success"),
        (DENIED, "Denied"),
        (FAILURE, "Failure"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    event_type = models.CharField(
        max_length=30,
        choices=EVENT_TYPE_CHOICES,
    )
    outcome = models.CharField(
        max_length=10,
        choices=OUTCOME_CHOICES,
    )
    details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    objects = AuditEventManager()

    def __str__(self):
        actor_name = self.actor.username if self.actor else "Anonymous/System"
        doc_title = self.document.title if self.document else "No Document"
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {self.event_type} - {self.outcome} (Actor: {actor_name}, Doc: {doc_title})"

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise TypeError("Audit events cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise TypeError("Audit events cannot be deleted.")
