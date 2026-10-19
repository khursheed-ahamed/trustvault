"""
Tests for document permission enforcement.

The key test proves that a viewer CANNOT download a document
they do not own and have not been explicitly granted access to.
"""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from accounts.models import User
from documents.models import Document, DocumentPermission
from audit.models import AuditEvent


class DocumentPermissionTests(TestCase):
    """Server-side access control tests for document downloads."""

    def setUp(self):
        """Create test users and a private document owned by the owner."""
        self.admin = User.objects.create_user(
            username="admin_user", password="testpass123", role=User.Role.ADMIN,
        )
        self.owner = User.objects.create_user(
            username="owner_user", password="testpass123", role=User.Role.OWNER,
        )
        self.viewer = User.objects.create_user(
            username="viewer_user", password="testpass123", role=User.Role.VIEWER,
        )

        # Create a private document owned by `owner`
        fake_file = SimpleUploadedFile(
            "secret_report.pdf",
            b"TOP SECRET CONTENT - do not share",
            content_type="application/pdf",
        )
        self.private_doc = Document.objects.create(
            title="Secret Report",
            file=fake_file,
            owner=self.owner,
            description="Owner's private document",
        )
        self.download_url = reverse(
            "documents:download", kwargs={"pk": self.private_doc.pk}
        )

    # ------------------------------------------------------------------ #
    #  THE KEY TEST — viewer cannot download owner's private document
    # ------------------------------------------------------------------ #
    def test_viewer_cannot_download_owners_private_document(self):
        """
        A viewer who does NOT own the document and has NOT been granted
        explicit access MUST receive a 403 Forbidden response.
        """
        client = Client()
        client.login(username="viewer_user", password="testpass123")

        response = client.get(self.download_url)

        self.assertEqual(response.status_code, 403)

        # Verify an audit event was logged for the denied access
        denied_event = AuditEvent.objects.filter(
            user=self.viewer,
            action="download_denied",
            resource_id=self.private_doc.pk,
        )
        self.assertTrue(denied_event.exists())

    # ------------------------------------------------------------------ #
    #  Supporting tests
    # ------------------------------------------------------------------ #
    def test_owner_can_download_own_document(self):
        """The document owner should be able to download their own file."""
        client = Client()
        client.login(username="owner_user", password="testpass123")

        response = client.get(self.download_url)

        self.assertEqual(response.status_code, 200)

    def test_admin_can_download_any_document(self):
        """An admin should be able to download any document."""
        client = Client()
        client.login(username="admin_user", password="testpass123")

        response = client.get(self.download_url)

        self.assertEqual(response.status_code, 200)

    def test_viewer_can_download_after_explicit_grant(self):
        """
        After the owner explicitly grants access, the viewer
        should be able to download the document.
        """
        DocumentPermission.objects.create(
            document=self.private_doc,
            user=self.viewer,
            granted_by=self.owner,
        )
        client = Client()
        client.login(username="viewer_user", password="testpass123")

        response = client.get(self.download_url)

        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_redirected_to_login(self):
        """An unauthenticated user should be redirected to the login page."""
        client = Client()

        response = client.get(self.download_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_user_has_access_method_returns_false_for_viewer(self):
        """Unit test on the model method itself."""
        self.assertFalse(self.private_doc.user_has_access(self.viewer))

    def test_user_has_access_method_returns_true_for_owner(self):
        """Unit test on the model method itself."""
        self.assertTrue(self.private_doc.user_has_access(self.owner))

    def test_user_has_access_method_returns_true_for_admin(self):
        """Unit test on the model method itself."""
        self.assertTrue(self.private_doc.user_has_access(self.admin))
