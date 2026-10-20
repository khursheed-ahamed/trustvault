from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from audit.models import AuditEvent
from documents.models import Document, DocumentPermission

User = get_user_model()


class DocumentPermissionSecurityTests(TestCase):
    """
    Automated security tests proving server-side document authorization.
    """

    def setUp(self):
        self.client = Client()

        # Create Owner User
        self.owner = User.objects.create_user(
            username="owner_user",
            password="TestPassword123!",
            role="OWNER",
        )

        # Create Viewer User
        self.viewer = User.objects.create_user(
            username="viewer_user",
            password="TestPassword123!",
            role="VIEWER",
        )

        # Create a private test document owned by self.owner
        test_file = SimpleUploadedFile(
            "internal_strategy.pdf",
            b"RESTRICTED: TrustVault Internal Strategy Document",
            content_type="application/pdf",
        )
        self.document = Document.objects.create(
            title="Internal Strategy 2026",
            file=test_file,
            original_filename="internal_strategy.pdf",
            category="Confidential",
            owner=self.owner,
        )

        self.detail_url = reverse(
            "documents:secure_document_detail",
            kwargs={"document_id": self.document.pk},
        )

    def test_owner_can_access_own_document(self):
        """1. An owner can open their own document detail URL and receives HTTP 200."""
        self.client.login(username="owner_user", password="TestPassword123!")
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.document.title)

    def test_viewer_with_no_permission_receives_403(self):
        """2. A viewer with no permission receives HTTP 403."""
        self.client.login(username="viewer_user", password="TestPassword123!")
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 403)

    def test_denied_attempt_creates_access_denied_audit_event(self):
        """
        3. The denied viewer attempt creates an AuditEvent with:
           - event_type = ACCESS_DENIED
           - outcome = DENIED
        """
        initial_event_count = AuditEvent.objects.count()

        self.client.login(username="viewer_user", password="TestPassword123!")
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(AuditEvent.objects.count(), initial_event_count + 1)

        latest_event = AuditEvent.objects.latest("created_at")
        self.assertEqual(latest_event.actor, self.viewer)
        self.assertEqual(latest_event.document, self.document)
        self.assertEqual(latest_event.event_type, AuditEvent.ACCESS_DENIED)
        self.assertEqual(latest_event.outcome, AuditEvent.DENIED)
        self.assertIn("read", latest_event.details.lower())

    def test_viewer_with_active_read_permission_receives_200(self):
        """4. A viewer with active READ permission receives HTTP 200."""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
        )

        self.client.login(username="viewer_user", password="TestPassword123!")
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.document.title)

    def test_viewer_with_active_edit_permission_receives_200(self):
        """5. A viewer with active EDIT permission receives HTTP 200."""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission=DocumentPermission.EDIT,
            granted_by=self.owner,
        )

        self.client.login(username="viewer_user", password="TestPassword123!")
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), self.document.title)

    def test_revoked_permission_causes_403(self):
        """6. A revoked permission causes HTTP 403."""
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
            revoked_at=timezone.now(),  # Revoked permission
        )

        self.client.login(username="viewer_user", password="TestPassword123!")
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, 403)

    def test_owner_cannot_grant_permission_to_self(self):
        """Owner validation rule: clean() raises ValidationError if granting to self."""
        perm = DocumentPermission(
            document=self.document,
            user=self.owner,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
        )
        with self.assertRaises(ValidationError):
            perm.clean()

    def test_unauthenticated_user_receives_403_and_denied_audit(self):
        """Unauthenticated requests are denied and audited."""
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, 403)

        latest_event = AuditEvent.objects.latest("created_at")
        self.assertIsNone(latest_event.actor)
        self.assertEqual(latest_event.event_type, AuditEvent.ACCESS_DENIED)
        self.assertEqual(latest_event.outcome, AuditEvent.DENIED)
