from django.contrib.admin.sites import site
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from audit.admin import AuditEventAdmin
from audit.models import AuditEvent
from documents.models import Document

User = get_user_model()


class AdminAuditDashboardTests(TestCase):
    """
    Automated security tests for the Administrator Audit Activity Dashboard.
    """

    def setUp(self):
        self.client = Client()
        self.rf = RequestFactory()

        # 1. Create Admin, Owner, and Viewer users
        self.admin = User.objects.create_user(
            username="admin_user",
            password="DemoPassword123!",
            role="ADMIN",
            is_staff=True,
            is_superuser=True,
        )
        self.owner = User.objects.create_user(
            username="owner_user",
            password="DemoPassword123!",
            role="OWNER",
        )
        self.viewer = User.objects.create_user(
            username="viewer_user",
            password="DemoPassword123!",
            role="VIEWER",
        )

        # 2. Create sample document
        mock_file = SimpleUploadedFile(
            "audit_target.pdf",
            b"%PDF-1.4 Mock content",
            content_type="application/pdf",
        )
        self.document = Document.objects.create(
            title="Confidential Audit Target",
            file=mock_file,
            original_filename="audit_target.pdf",
            owner=self.owner,
        )

        # 3. Create sample audit events
        self.event_upload = AuditEvent.objects.create(
            actor=self.owner,
            document=self.document,
            event_type=AuditEvent.UPLOAD,
            outcome=AuditEvent.SUCCESS,
            details="Owner uploaded confidential audit target.",
        )
        self.event_denied = AuditEvent.objects.create(
            actor=self.viewer,
            document=self.document,
            event_type=AuditEvent.ACCESS_DENIED,
            outcome=AuditEvent.DENIED,
            details="Viewer was denied access.",
        )

        self.dashboard_url = reverse("admin_audit_dashboard")

    # 1. An ADMIN user receives HTTP 200.
    def test_admin_user_receives_200(self):
        self.client.login(username="admin_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Audit & Activity Dashboard")

    # 2. An OWNER user receives HTTP 403.
    def test_owner_user_receives_403(self):
        self.client.login(username="owner_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    # 3. A VIEWER user receives HTTP 403.
    def test_viewer_user_receives_403(self):
        self.client.login(username="viewer_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 403)

    # 4. An unauthenticated user is redirected to login.
    def test_unauthenticated_user_redirected_to_login(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    # 5. Event-type and outcome filters work.
    def test_event_type_and_outcome_filters(self):
        self.client.login(username="admin_user", password="DemoPassword123!")

        # Filter by event_type=ACCESS_DENIED
        response = self.client.get(self.dashboard_url, {"event_type": AuditEvent.ACCESS_DENIED})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Viewer was denied access.")
        self.assertNotContains(response, "Owner uploaded confidential audit target.")

        # Filter by outcome=SUCCESS
        response = self.client.get(self.dashboard_url, {"outcome": AuditEvent.SUCCESS})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Owner uploaded confidential audit target.")
        self.assertNotContains(response, "Viewer was denied access.")

    # 6. The response does not contain a document storage path or MEDIA_URL.
    def test_response_does_not_contain_storage_path_or_media_url(self):
        self.client.login(username="admin_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()

        self.assertNotIn(self.document.file.name, content)
        self.assertNotIn("/media/", content)

    # 7. Audit events cannot be changed or deleted through Django admin.
    def test_audit_admin_is_strictly_read_only(self):
        admin_obj = AuditEventAdmin(AuditEvent, site)
        request = self.rf.get("/admin/audit/auditevent/")
        request.user = self.admin

        self.assertFalse(admin_obj.has_add_permission(request))
        self.assertFalse(admin_obj.has_change_permission(request, self.event_upload))
        self.assertFalse(admin_obj.has_delete_permission(request, self.event_upload))
