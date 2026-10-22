from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from documents.models import Document, DocumentPermission

User = get_user_model()


class DocumentSearchSecurityTests(TestCase):
    """
    Automated security tests for scoped document search on the dashboard.
    """

    def setUp(self):
        self.client = Client()

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

        test_file = SimpleUploadedFile(
            "finance_strategy.pdf",
            b"%PDF-1.4 Mock confidential report",
            content_type="application/pdf",
        )
        self.doc = Document.objects.create(
            title="Secret Finance Strategy",
            file=test_file,
            original_filename="finance_strategy.pdf",
            category="Finances",
            owner=self.owner,
        )

        self.dashboard_url = reverse("document_dashboard")

    # 1. An owner sees their own document.
    def test_owner_sees_own_document_in_search(self):
        self.client.login(username="owner_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url, {"q": "Secret"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secret Finance Strategy")

    # 2. A viewer with no active permission does not see the owner's document.
    def test_viewer_without_permission_cannot_see_or_search_document(self):
        self.client.login(username="viewer_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url, {"q": "Secret"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Secret Finance Strategy")

    # 3. A viewer with active READ permission sees the document.
    def test_viewer_with_active_permission_sees_document(self):
        DocumentPermission.objects.create(
            document=self.doc,
            user=self.viewer,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
        )
        self.client.login(username="viewer_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url, {"q": "Secret"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Secret Finance Strategy")

    # 4. A revoked viewer does not see the document.
    def test_revoked_viewer_does_not_see_document_in_search(self):
        DocumentPermission.objects.create(
            document=self.doc,
            user=self.viewer,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
            revoked_at=timezone.now(),  # Explicitly revoked
        )
        self.client.login(username="viewer_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url, {"q": "Secret"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Secret Finance Strategy")

    # 5. Title, owner, category, and date filters work.
    def test_title_owner_category_and_date_filters(self):
        self.client.login(username="owner_user", password="DemoPassword123!")

        # Title match
        res_title = self.client.get(self.dashboard_url, {"q": "Finance"})
        self.assertContains(res_title, "Secret Finance Strategy")

        # Owner match
        res_owner = self.client.get(self.dashboard_url, {"owner": "owner_user"})
        self.assertContains(res_owner, "Secret Finance Strategy")

        # Category match
        res_cat = self.client.get(self.dashboard_url, {"category": "Finances"})
        self.assertContains(res_cat, "Secret Finance Strategy")

        # Category mismatch
        res_cat_mismatch = self.client.get(self.dashboard_url, {"category": "HR"})
        self.assertNotContains(res_cat_mismatch, "Secret Finance Strategy")

        # Date filter match
        today = timezone.now().date().strftime("%Y-%m-%d")
        res_date = self.client.get(self.dashboard_url, {"uploaded_from": today, "uploaded_to": today})
        self.assertContains(res_date, "Secret Finance Strategy")

    # 6. Invalid dates return a normal page with a validation error.
    def test_invalid_dates_return_200_with_form_validation_error(self):
        self.client.login(username="owner_user", password="DemoPassword123!")
        response = self.client.get(self.dashboard_url, {"uploaded_from": "not-a-date"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search input error")
        self.assertContains(response, "Enter a valid upload date in YYYY-MM-DD format.")

    # 7. Search results never include unauthorized document metadata.
    def test_search_results_never_include_unauthorized_metadata(self):
        self.client.login(username="viewer_user", password="DemoPassword123!")
        # Search using owner's username
        response = self.client.get(self.dashboard_url, {"owner": "owner_user"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Secret Finance Strategy")
        self.assertNotContains(response, "finance_strategy.pdf")
        self.assertNotContains(response, "Finances")
