# AI Usage Log — TrustVault

## 2026-10-19 — Project setup

**Prompt:** Asked for a beginner-friendly Python and Django setup for the TrustVault secure document-sharing project.

**AI output:** Suggested creating a Django project with three apps: `accounts`, `documents`, and `audit`.

**What I did:** Created the Django project and the three apps in VS Code. Added them to `INSTALLED_APPS` and confirmed the Django development server runs.

**What I checked:** Opened `http://127.0.0.1:8000/` and confirmed Django starts without errors.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-19 — Security documentation

**Prompt:** Asked what documentation must be included for the TrustVault challenge.

**AI output:** Suggested creating `README.md`, `THREATS.md`, and `PROMPTS.md`.

**What I did:** Created the documentation files at the project root before building the main features.

**What I checked:** Confirmed the files are included in the Git repository and are not ignored by `.gitignore`.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-20 — User roles

**Prompt:** Asked for an implementation plan for Django users with Admin, Owner, and Viewer roles.

**AI output:** Suggested extending Django’s `AbstractUser` model with a role field.

**What I did:** Created a custom User model with the roles `ADMIN`, `OWNER`, and `VIEWER`. The default role is `VIEWER`.

**What I checked:** Used the Django admin panel and demo accounts to confirm each account has the intended role.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-20 — Important access-control check

**Prompt:** Asked how document permission should work.

**AI output:** Suggested allowing access if a user is an owner or has a named permission grant.

**Potential problem identified:** It would be unsafe to check permissions only in the webpage or hide buttons in the user interface. A user could call a download URL or API route directly.

**What I will do instead:** Every document view, download, update, delete, and search request will perform a server-side authorization check. The user interface will not be trusted as the security boundary.

**How I will test it:** An automated test will make Viewer B request Owner A’s private document and must receive `403 Forbidden`.

**Commit:** Add the GitHub commit link after this security feature is implemented.

## 2026-10-21 — Document permission model

**Prompt:** Asked AI to generate Django models for documents and named permissions.

**AI output:** Proposed a `DocumentPermission` model with `READ` and `EDIT` permissions.

**What I did:** Added a permission record for one named user and one document, including who granted it, when it was granted, and when it was revoked.

**What I checked:** Confirmed one user cannot have duplicate permission records for the same document.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-21 — Server-side authorization

**Prompt:** Asked AI to create the central document-access rule.

**AI output:** Suggested a `can_access_document(user, document, action)` function.

**Potential problem identified:** An authorization check only on a document webpage would not protect other routes, such as downloads, edits, or future API endpoints.

**What I did instead:** Created one server-side authorization function. The document owner has full access; an active `READ` permission allows reading only; an active `EDIT` permission allows reading and editing. No one else has access.

**How I tested it:** Tested owner access, no-permission denial, `READ` access, `EDIT` access, and revoked-access denial.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-21 — Denied-access audit logging

**Prompt:** Asked AI how to audit unauthorized document attempts.

**AI output:** Suggested recording denied access in an `AuditEvent`.

**Potential problem identified:** If a denied request only returns `403 Forbidden` without an audit record, the administrator cannot later prove that the access attempt occurred.

**What I did instead:** Added `record_access_denied()` to create an audit event with `ACCESS_DENIED`, `DENIED`, the attempted action, the user, and the document.

**How I tested it:** Made a viewer without permission request an owner’s document, checked for HTTP `403`, and confirmed that an audit event was created.

**Commit:** Add the GitHub commit link after committing this work.

## 2026-10-21 — Secure upload and download pages

**Prompt:** Asked AI to generate Django pages for secure upload, document details, download, permission grants, and revocation.

**AI output:** Suggested Django forms, protected Django views, and templates for the user-facing document workflow.

**What I did:** Added owner-only upload, an authorized document dashboard, protected document details, protected download, permission grant, and permission revocation features.

**What I checked:** Confirmed that access decisions happen in Django views through `can_access_document()` and not only by hiding buttons in templates.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-21 — PDF download investigation

**Prompt:** Asked why a downloaded PDF did not open in its original format.

**AI output:** Initially reviewed the secure download view and confirmed it used `FileResponse`.

**What was wrong or incomplete:** The download code was not the cause. The test files were mock text bytes named with a `.pdf` extension, not real valid PDF files.

**What I did instead:** Kept the secure `FileResponse` download implementation and tested manual uploads using a genuine PDF file from the computer.

**What I checked:** Confirmed the download route does not use a public file URL and returns the stored file bytes through Django.

**Commit:** Add the GitHub commit link after committing this work.

---

## 2026-10-21 — Upload-template mismatch

**Prompt:** Asked AI to inspect the upload page after checking document download behavior.

**AI output:** Identified that the view expected `documents/document_upload.html`, but an existing template was named `upload.html`.

**What was wrong:** The template also used a `description` field while the Django upload form expects `category`.

**What I did instead:** Renamed the template to match the view and changed the form fields to `title`, `category`, and `file`.

**What I checked:** Confirmed the upload form uses `enctype="multipart/form-data"` so the browser sends the selected file correctly.

**Commit:** Add the GitHub commit link after committing this work.

## 2026-10-22 — Admin audit dashboard

**Prompt:** Asked AI to create an administrator-only audit activity dashboard for TrustVault.

**AI output:** Suggested an `admin_audit_dashboard` view with filters for event type, outcome, actor, document, and date.

**What I checked:** The project did not need a separate `audit/urls.py` because the dashboard route was connected directly in `trustvault/urls.py` at `/activity/`.

**What I did:** Restricted the view using the custom user role `ADMIN`, added audit filters, and kept audit records read-only.

**Security check:** Owners and viewers receive `403 Forbidden`. The view does not expose document file URLs.

**Commit:** Add the GitHub commit link here.

---

## 2026-10-22 — Search authorization

**Prompt:** Asked AI to add document search by title, owner, category, and upload date.

**AI output:** Suggested a `DocumentSearchForm` and database filtering in the dashboard view.

**Potential problem identified:** Filtering only in the template could reveal unauthorized document metadata.

**What I did instead:** Applied the owner-or-active-permission authorization query before search filters and used `distinct()` to avoid duplicate results.

**How I tested it:** Confirmed an unshared viewer cannot see another owner’s document in search, while a viewer with active permission can.

**Commit:** Add the GitHub commit link here.

---

## 2026-10-22 — PDF signature validation

**Prompt:** Asked AI to prevent text files renamed with a `.pdf` extension from being uploaded.

**AI output:** Suggested checking that PDF uploads begin with the `%PDF-` signature.

**What I did:** Added a five-byte signature check, restored the uploaded file pointer with `seek(0)`, and retained the 10 MB size limit and extension validation.

**Limitation:** This is basic file validation, not antivirus scanning. DOCX validation remains limited to extension and size checks.

**How I tested it:** A fake text file named `fake.pdf` is rejected, while a real PDF beginning with `%PDF-` passes.

**Commit:** Add the GitHub commit link here.