from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from documents.forms import DocumentUploadForm


class DocumentUploadValidationTests(TestCase):
    """
    Automated security tests for upload validation, including PDF magic-byte checks.
    """

    # 1. A real-looking upload beginning with %PDF- passes the PDF signature check.
    def test_valid_pdf_signature_passes(self):
        valid_pdf = SimpleUploadedFile(
            "valid.pdf",
            b"%PDF-1.4 standard valid pdf header content",
            content_type="application/pdf",
        )
        form = DocumentUploadForm(
            data={"title": "Valid PDF Doc", "category": "Legal"},
            files={"file": valid_pdf},
        )
        self.assertTrue(form.is_valid())

    # 2. A file named fake.pdf containing ordinary text is rejected.
    def test_fake_pdf_missing_magic_bytes_rejected(self):
        fake_pdf = SimpleUploadedFile(
            "fake.pdf",
            b"This is just plain text renamed to pdf.",
            content_type="application/pdf",
        )
        form = DocumentUploadForm(
            data={"title": "Fake PDF Doc"},
            files={"file": fake_pdf},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
        self.assertIn("does not begin with the standard '%PDF-' signature", form.errors["file"][0])

    # 3. A file larger than 10 MB is rejected.
    def test_file_larger_than_10mb_rejected(self):
        # 10 MB + 1 byte
        oversized_content = b"0" * (10 * 1024 * 1024 + 1)
        oversized_file = SimpleUploadedFile(
            "huge.txt",
            oversized_content,
            content_type="text/plain",
        )
        form = DocumentUploadForm(
            data={"title": "Huge Document"},
            files={"file": oversized_file},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
        self.assertIn("exceeds the 10 MB limit", form.errors["file"][0])

    # 4. A disallowed extension is rejected.
    def test_disallowed_extension_rejected(self):
        script_file = SimpleUploadedFile(
            "malicious.sh",
            b"#!/bin/bash\necho dangerous",
            content_type="application/x-sh",
        )
        form = DocumentUploadForm(
            data={"title": "Script File"},
            files={"file": script_file},
        )
        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)
        self.assertIn("Invalid file extension", form.errors["file"][0])

    # 5. After validation, the upload file pointer is correctly reset.
    def test_file_pointer_reset_after_validation(self):
        valid_pdf = SimpleUploadedFile(
            "pointer_test.pdf",
            b"%PDF-1.7 Content testing seek reset",
            content_type="application/pdf",
        )
        form = DocumentUploadForm(
            data={"title": "Pointer Test"},
            files={"file": valid_pdf},
        )
        self.assertTrue(form.is_valid())
        # The file pointer on the cleaned file must be at position 0
        cleaned_file = form.cleaned_data["file"]
        self.assertEqual(cleaned_file.tell(), 0)
