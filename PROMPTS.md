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

---

## 2026-10-22 — production deployment and final security

**Prompt or summary:** Asked AI to inspect the existing TrustVault project and implement production settings, private S3-compatible storage, deployment files, route documentation, final security tests, and a live deployment checklist without replacing existing authorization behavior.

**AI output:** Added environment-driven production configuration, PostgreSQL parsing, private local/S3 storage backends, Render/Gunicorn deployment configuration, a non-sensitive health route, route and deployment documentation, and regression tests for production settings, revocation, protected downloads, audit immutability, and health output.

**Specific mistake or risk discovered:** The existing settings contained a hard-coded development signing-key placeholder, wildcard allowed hosts, and a `/media/` URL configuration. Local filesystem storage also has no provider policy to enforce privacy. The old placeholder remains in earlier Git history, so it must be treated as public and not reused. A deployment must not be described as live-tested before it is actually deployed.

**Correction made:** Removed the key from current settings and removed the wildcard host default; production now requires an explicit secret, host allowlist, PostgreSQL URL, and S3-compatible credentials. Storage URL generation is disabled, and the existing download route retains its server-side permission check before opening file bytes. Added explicit production-settings and no-public-media tests, and documented private bucket policy requirements and the manual live checklist.

**Verification status:** Automated checks and tests must be run locally before commit. The live checklist remains unverified until a deployment is performed.

**Commit link:** `<add-after-commit>`


## 2026-10-22 — Production configuration

**Prompt:** Asked AI to prepare TrustVault for deployment with environment-based secrets, PostgreSQL, private storage, and secure production settings.

**AI output:** Suggested production settings, `.env.example`, deployment files, Gunicorn, and private object storage.

**What I checked:** Confirmed secrets are read from environment variables, `.env` is ignored, and local SQLite development still works when `DATABASE_URL` is absent.

**What I did:** Added production configuration and documented the required deployment variables without committing real credentials.

**Commit:** Add the GitHub commit link here.

---

## 2026-10-22 — Health endpoint and live verification

**Prompt:** Asked AI how to verify that the deployed TrustVault application is running.

**AI output:** Suggested a simple `/health/` endpoint returning HTTP 200 without exposing user or secret data.

**What I did:** Added or verified the health endpoint and tested it locally with the browser and PowerShell.

**What I checked:** Confirmed the endpoint returns `200`, while protected document routes still require authentication and authorization.

**Commit:** Add the GitHub commit link here.

---

## 2026-10-22 — Final security testing

**Prompt:** Asked AI for a final live-deployment security checklist.

**AI output:** Suggested testing role boundaries, search privacy, revocation, secure downloads, audit events, and invalid uploads.

**What I did:** Tested the live or local application with Admin, Owner, and Viewer accounts. Verified that unauthorized access returns `403`, revocation works immediately, and denied attempts create audit events.

**What I checked:** Ran `python manage.py check` and `python manage.py test`.

**Commit:** Add the GitHub commit link here.