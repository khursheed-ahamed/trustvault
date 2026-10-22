import json
import os
import subprocess
import sys
from datetime import datetime, timezone as datetime_timezone
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.deletion import ProtectedError
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from audit.models import AuditEvent
from documents.models import Document, DocumentPermission
from documents.storage import PrivateS3Storage
from trustvault.urls import urlpatterns

User = get_user_model()


class FinalSecurityTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="final_owner",
            password="test-password-only",
            role="OWNER",
        )
        self.viewer = User.objects.create_user(
            username="final_viewer",
            password="test-password-only",
            role="VIEWER",
        )
        self.document = Document.objects.create(
            title="Private report",
            file=SimpleUploadedFile(
                "private.pdf",
                b"%PDF-1.4 test document",
                content_type="application/pdf",
            ),
            original_filename="private.pdf",
            owner=self.owner,
        )

    def test_production_settings_disable_debug_and_enable_https_security(self):
        environment = os.environ.copy()
        environment.update(
            {
                "DJANGO_ENV": "production",
                "SECRET_KEY": "unit-test-secret-key",
                "ALLOWED_HOSTS": "example.test",
                "CSRF_TRUSTED_ORIGINS": "https://example.test",
                "DATABASE_URL": "postgresql://localhost/trustvault_test",
                "AWS_ACCESS_KEY_ID": "unit-test-access-key",
                "AWS_SECRET_ACCESS_KEY": "unit-test-secret-key",
                "AWS_STORAGE_BUCKET_NAME": "unit-test-bucket",
                "AWS_S3_REGION_NAME": "us-east-1",
                "AWS_S3_SIGNATURE_VERSION": "s3v4",
            }
        )
        environment.pop("DEBUG", None)
        code = (
            "import json, trustvault.settings as s; "
            "print(json.dumps({"
            "'debug': s.DEBUG, 'production': s.PRODUCTION, "
            "'database': s.DATABASES['default']['ENGINE'], "
            "'redirect': s.SECURE_SSL_REDIRECT, "
            "'session_cookie': s.SESSION_COOKIE_SECURE, "
            "'csrf_cookie': s.CSRF_COOKIE_SECURE, "
            "'allowed_hosts': s.ALLOWED_HOSTS, "
            "'csrf_origins': s.CSRF_TRUSTED_ORIGINS, "
            "'storage_backend': s.STORAGES['default']['BACKEND'], "
            "'storage_acl': s.STORAGES['default']['OPTIONS']['default_acl'], "
            "'storage_querystring_auth': "
            "s.STORAGES['default']['OPTIONS']['querystring_auth'], "
            "'storage_custom_domain': "
            "s.STORAGES['default']['OPTIONS']['custom_domain']}))"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[2],
            env=environment,
            capture_output=True,
            check=True,
            text=True,
        )

        production_settings = json.loads(result.stdout)
        self.assertFalse(production_settings["debug"])
        self.assertTrue(production_settings["production"])
        self.assertEqual(
            production_settings["database"],
            "django.db.backends.postgresql",
        )
        self.assertTrue(production_settings["redirect"])
        self.assertTrue(production_settings["session_cookie"])
        self.assertTrue(production_settings["csrf_cookie"])
        self.assertEqual(production_settings["allowed_hosts"], ["example.test"])
        self.assertEqual(
            production_settings["csrf_origins"],
            ["https://example.test"],
        )
        self.assertEqual(
            production_settings["storage_backend"],
            "documents.storage.PrivateS3Storage",
        )
        self.assertIsNone(production_settings["storage_acl"])
        self.assertTrue(production_settings["storage_querystring_auth"])
        self.assertIsNone(production_settings["storage_custom_domain"])

    def test_media_is_not_routed_and_document_storage_has_no_url(self):
        self.assertFalse(settings.is_overridden("MEDIA_URL"))
        self.assertFalse(any("media" in str(pattern.pattern).lower() for pattern in urlpatterns))
        with self.assertRaises(ValueError):
            self.document.file.url
        with self.assertRaises(ValueError):
            PrivateS3Storage(bucket_name="unit-test-bucket").url("object-key")

    def test_revoked_permission_denies_detail_and_does_not_open_file(self):
        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            permission=DocumentPermission.READ,
            granted_by=self.owner,
        )
        self.client.force_login(self.viewer)
        download_url = reverse(
            "secure_document_download",
            kwargs={"document_id": self.document.pk},
        )
        self.assertEqual(self.client.get(download_url).status_code, 200)

        permission.revoked_at = timezone.now()
        permission.save()
        storage = self.document.file.storage
        with patch.object(storage, "open", wraps=storage.open) as storage_open:
            self.assertEqual(
                self.client.get(
                    reverse(
                        "secure_document_detail",
                        kwargs={"document_id": self.document.pk},
                    )
                ).status_code,
                403,
            )
            self.assertEqual(self.client.get(download_url).status_code, 403)
            storage_open.assert_not_called()

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.viewer,
                document=self.document,
                event_type=AuditEvent.ACCESS_DENIED,
                outcome=AuditEvent.DENIED,
            ).exists()
        )

    def test_health_check_is_public_and_contains_no_sensitive_data(self):
        response = self.client.get(reverse("health_check"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")
        self.assertEqual(response["Content-Type"], "text/plain")
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertNotIn(settings.SECRET_KEY.encode(), response.content)

    def test_document_and_audit_timestamps_render_in_configured_local_timezone(self):
        self.assertEqual(settings.TIME_ZONE, "Asia/Kolkata")
        self.assertTrue(settings.USE_TZ)
        uploaded_at = datetime(2026, 10, 22, 12, 30, tzinfo=datetime_timezone.utc)
        Document.objects.filter(pk=self.document.pk).update(created_at=uploaded_at)

        self.client.force_login(self.owner)
        detail_response = self.client.get(
            reverse(
                "secure_document_detail",
                kwargs={"document_id": self.document.pk},
            )
        )
        dashboard_response = self.client.get(reverse("document_dashboard"))
        self.assertContains(detail_response, "October 22, 2026, 18:00")
        self.assertContains(dashboard_response, "2026-10-22 18:00")

        admin = User.objects.create_user(
            username="final_admin",
            password="test-password-only",
            role="ADMIN",
            is_staff=True,
        )
        event = AuditEvent.objects.create(
            actor=self.owner,
            document=self.document,
            event_type=AuditEvent.UPLOAD,
            outcome=AuditEvent.SUCCESS,
        )
        self.client.force_login(admin)
        audit_response = self.client.get(reverse("admin_audit_dashboard"))
        local_event_time = timezone.localtime(event.created_at).strftime("%Y-%m-%d %H:%M:%S")
        self.assertContains(audit_response, local_event_time)

    def test_audit_events_are_append_only_through_model_and_queryset(self):
        event = AuditEvent.objects.create(
            actor=self.owner,
            document=self.document,
            event_type=AuditEvent.VIEW,
            outcome=AuditEvent.SUCCESS,
            details="Original entry",
        )
        event.details = "Modified entry"
        with self.assertRaises(TypeError):
            event.save()
        with self.assertRaises(TypeError):
            event.delete()
        with self.assertRaises(TypeError):
            AuditEvent.objects.filter(pk=event.pk).update(details="Modified entry")
        with self.assertRaises(TypeError):
            AuditEvent.objects.filter(pk=event.pk).delete()
        with self.assertRaises(ProtectedError):
            self.document.delete()

        event.refresh_from_db()
        self.assertEqual(event.details, "Original entry")
        self.assertTrue(Document.objects.filter(pk=self.document.pk).exists())
