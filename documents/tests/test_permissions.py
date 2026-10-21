from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from audit.models import AuditEvent
from documents.models import Document, DocumentPermission

User = get_user_model()


class DocumentSecurityAndPermissionTests(TestCase):
    """
    Day-4 automated test suite validating:
    - Role-based upload restrictions
    - Server-side download authorization
    - Access denial audit logging
    - Dynamic grant and revocation lifecycles
    - Absolute prevention of public/storage file URL exposure
    """

    def setUp(self):
        self.client = Client()

        # 1. Create Owner User
        self.owner = User.objects.create_user(
            username="owner_user",
            password="DemoPassword123!",
            role="OWNER",
        )

        # 2. Create Viewer User
        self.viewer = User.objects.create_user(
            username="viewer_user",
            password="DemoPassword123!",
            role="VIEWER",
        )

        # 3. Create a second Viewer User for permission testing
        self.viewer2 = User.objects.create_user(
            username="viewer2_user",
            password="DemoPassword123!",
            role="VIEWER",
        )

        # 4. Create sample document owned by self.owner
        test_file = SimpleUploadedFile(
            "financial_audit_q3.pdf",
            b"%PDF-1.4 Mock confidential PDF binary stream for testing.",
            content_type="application/pdf",
        )
        self.document = Document.objects.create(
            title="Q3 Financial Audit",
            file=test_file,
            original_filename="financial_audit_q3.pdf",
            category="Finance",
            owner=self.owner,
        )

        self.detail_url = reverse(
            "secure_document_detail",
            kwargs={"document_id": self.document.pk},
        )
        self.download_url = reverse(
            "secure_document_download",
            kwargs={"document_id": self.document.pk},
        )
        self.manage_perms_url = reverse(
            "manage_document_permissions",
            kwargs={"document_id": self.document.pk},
        )

    # 1. An owner with role OWNER can upload a valid .pdf document and receives a redirect.
    def test_owner_can_upload_valid_pdf_document_and_receives_redirect(self):
        self.client.login(username="owner_user", password="DemoPassword123!")

        new_pdf = SimpleUploadedFile(
            "board_minutes.pdf",
            b"%PDF-1.4 Board meeting minutes.",
            content_type="application/pdf",
        )
        response = self.client.post(
            reverse("document_upload"),
            {
                "title": "Board Minutes 2026",
                "category": "Corporate",
                "file": new_pdf,
            },
        )

        # Must redirect to document detail page
        self.assertEqual(response.status_code, 302)
        new_doc = Document.objects.get(title="Board Minutes 2026")
        self.assertEqual(new_doc.owner, self.owner)
        self.assertEqual(new_doc.original_filename, "board_minutes.pdf")

        # Verify UPLOAD audit event was recorded
        upload_event = AuditEvent.objects.filter(
            actor=self.owner,
            document=new_doc,
            event_type=AuditEvent.UPLOAD,
            outcome=AuditEvent.SUCCESS,
        )
        self.assertTrue(upload_event.exists())

    # 2. A viewer attempting the upload route receives HTTP 403.
    def test_viewer_attempting_upload_route_receives_403(self):
        self.client.login(username="viewer_user", password="DemoPassword123!")

        # Both GET and POST must be rejected with 403
        response_get = self.client.get(reverse("document_upload"))
        self.assertEqual(response_get.status_code, 403)

        fake_pdf = SimpleUploadedFile("viewer.pdf", b"content", content_type="application/pdf")
        response_post = self.client.post(
            reverse("document_upload"),
            {"title": "Viewer Upload", "file": fake_pdf},
        )
        self.assertEqual(response_post.status_code, 403)

    # 3. An owner can download their own document and receives HTTP 200.
    def test_owner_can_download_own_document_and_receives_200(self):
        self.client.login(username="owner_user", password="DemoPassword123!")

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("financial_audit_q3.pdf", response.headers.get("Content-Disposition", ""))

        # Verify DOWNLOAD audit event
        download_event = AuditEvent.objects.filter(
            actor=self.owner,
            document=self.document,
            event_type=AuditEvent.DOWNLOAD,
            outcome=AuditEvent.SUCCESS,
        )
        self.assertTrue(download_event.exists())

    # 4. A viewer without permission receives HTTP 403 for download.
    def test_viewer_without_permission_receives_403_for_download(self):
        self.client.login(username="viewer_user", password="DemoPassword123!")

        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 403)

    # 5. The denied viewer download creates an AuditEvent with: event_type=ACCESS_DENIED, outcome=DENIED.
    def test_denied_viewer_download_creates_access_denied_audit_event(self):
        initial_denied_count = AuditEvent.objects.filter(
            actor=self.viewer,
            event_type=AuditEvent.ACCESS_DENIED,
            outcome=AuditEvent.DENIED,
        ).count()

        self.client.login(username="viewer_user", password="DemoPassword123!")
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, 403)

        new_denied_count = AuditEvent.objects.filter(
            actor=self.viewer,
            event_type=AuditEvent.ACCESS_DENIED,
            outcome=AuditEvent.DENIED,
        ).count()
        self.assertEqual(new_denied_count, initial_denied_count + 1)

        latest_event = AuditEvent.objects.filter(
            actor=self.viewer,
            document=self.document,
        ).latest("created_at")
        self.assertEqual(latest_event.event_type, AuditEvent.ACCESS_DENIED)
        self.assertEqual(latest_event.outcome, AuditEvent.DENIED)
        self.assertIn("download", latest_event.details.lower())

    # 6. Grant READ permission to a viewer; the viewer download returns HTTP 200.
    def test_grant_read_permission_allows_viewer_download_with_200(self):
        self.client.login(username="owner_user", password="DemoPassword123!")

        # Owner grants READ permission via POST form
        response = self.client.post(
            self.manage_perms_url,
            {
                "user": self.viewer.pk,
                "permission": DocumentPermission.READ,
            },
        )
        self.assertEqual(response.status_code, 302)

        # Viewer can now download successfully
        self.client.login(username="viewer_user", password="DemoPassword123!")
        download_response = self.client.get(self.download_url)
        self.assertEqual(download_response.status_code, 200)

    # 7. Revoke the same permission through the owner-only POST route; viewer's next download returns 403.
    def test_revoke_permission_via_post_causes_immediate_403_on_download(self):
        # 1. Set up active permission
        perm = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
        )

        # 2. Owner revokes it via owner-only POST route
        self.client.login(username="owner_user", password="DemoPassword123!")
        revoke_url = reverse(
            "revoke_document_permission",
            kwargs={"document_id": self.document.pk, "permission_id": perm.pk},
        )
        revoke_response = self.client.post(revoke_url)
        self.assertEqual(revoke_response.status_code, 302)

        # Verify DB state
        perm.refresh_from_db()
        self.assertFalse(perm.is_active)
        self.assertIsNotNone(perm.revoked_at)

        # 3. Viewer's immediate next download attempt MUST fail with 403
        self.client.login(username="viewer_user", password="DemoPassword123!")
        download_response = self.client.get(self.download_url)
        self.assertEqual(download_response.status_code, 403)

        # 4. Viewer's detail request MUST also fail with 403
        detail_response = self.client.get(self.detail_url)
        self.assertEqual(detail_response.status_code, 403)

    # 8. A non-owner attempting to open the permission-management route receives HTTP 403.
    def test_non_owner_attempting_permission_management_receives_403(self):
        self.client.login(username="viewer_user", password="DemoPassword123!")

        # GET request to permission management must be 403
        get_response = self.client.get(self.manage_perms_url)
        self.assertEqual(get_response.status_code, 403)

        # POST request to grant permission must also be 403
        post_response = self.client.post(
            self.manage_perms_url,
            {"user": self.viewer2.pk, "permission": DocumentPermission.READ},
        )
        self.assertEqual(post_response.status_code, 403)

    # 9. Verify no response HTML includes the file's storage URL or document.file.url.
    def test_no_response_html_includes_storage_or_file_url(self):
        self.client.login(username="owner_user", password="DemoPassword123!")

        # Check Dashboard page
        dashboard_res = self.client.get(reverse("document_dashboard"))
        self.assertEqual(dashboard_res.status_code, 200)
        self.assertNotIn(self.document.file.name, dashboard_res.content.decode())
        self.assertNotIn(settings.MEDIA_URL, dashboard_res.content.decode())

        # Check Detail page
        detail_res = self.client.get(self.detail_url)
        self.assertEqual(detail_res.status_code, 200)
        self.assertNotIn(self.document.file.name, detail_res.content.decode())
        self.assertNotIn(settings.MEDIA_URL, detail_res.content.decode())

        # Check Manage Permissions page
        perms_res = self.client.get(self.manage_perms_url)
        self.assertEqual(perms_res.status_code, 200)
        self.assertNotIn(self.document.file.name, perms_res.content.decode())
        self.assertNotIn(settings.MEDIA_URL, perms_res.content.decode())
