# Threat Model — TrustVault

## Security goal

TrustVault must ensure that only explicitly authorised users can access a document. The server must make every authorization decision. Hiding buttons or pages in the user interface is not sufficient.

## Assets to protect

- Uploaded document files
- Document titles, categories, owners, and other metadata
- User accounts and passwords
- Permission grants and revocations
- Audit records
- Secret keys and database credentials

## Threat 1 — Insecure Direct Object Reference (IDOR)

**Attack:** A logged-in user changes a document ID in a URL, for example from `/documents/1/` to `/documents/2/`.

**Impact:** The user may view, download, edit, or delete another user’s confidential document.

**Mitigation:** Every document-related Django view loads the document and uses one central server-side permission function before returning metadata or file content.

**Test:** Viewer B requests Owner A’s private document and receives `403 Forbidden`.

**Residual risk:** A new route could accidentally omit the central permission function. All new document routes must be reviewed and tested.

---

## Threat 2 — Download after access is revoked

**Attack:** A viewer uses a saved or old download link after an owner revokes their access.

**Impact:** Revoked users could continue accessing confidential documents.

**Mitigation:** Files will not have permanent public URLs. Every download request checks the current permission record in the database before sending file bytes.

**Test:** Grant a viewer access, confirm download works, revoke access, then confirm the same download route returns `403 Forbidden`.

**Residual risk:** A user may keep a file they downloaded before revocation. Technical controls cannot remove a copy already saved to their device.

---

## Threat 3 — Public uploaded files

**Attack:** A person guesses or obtains a direct media/storage URL.

**Impact:** Anyone with the URL could download a confidential file without logging in.

**Mitigation:** Production storage will be private. Documents will be served only through a Django download view after authorization succeeds.

**Test:** Attempt to access a stored file directly without authentication; access must fail.

**Residual risk:** Incorrect cloud-storage configuration could make files public. Deployment settings must be checked manually.

---

## Threat 4 — Unauthorized permission changes

**Attack:** A viewer or editor sends a request that grants themselves access, grants another user access, or removes the owner’s access.

**Impact:** Unauthorized users can expand their own permissions.

**Mitigation:** Only the document owner can grant or revoke permissions. The server verifies ownership before changing permission records.

**Test:** A non-owner attempts to create or delete a permission grant and receives `403 Forbidden`.

---

## Threat 5 — Search leaks private document metadata

**Attack:** A user searches for documents they cannot access.

**Impact:** Titles, owners, categories, or dates may expose confidential information even if file download is blocked.

**Mitigation:** Search queries will be filtered on the server to return only documents owned by the user or explicitly shared with them.

**Test:** Viewer B searches for Owner A’s private document; it must not appear in results.

---

## Threat 6 — Dangerous file upload

**Attack:** A user uploads a malicious executable, an oversized file, a file with a fake extension, or a path-traversal filename.

**Impact:** Malware delivery, denial of service, or unsafe file handling.

**Mitigation:** Validate allowed file types, file size, filename length, MIME type, and file signature where practical. Generate storage names on the server and never use user filenames as file paths.

**Test:** Upload invalid or oversized files and confirm that Django rejects them.

---

## Threat 7 — Missing or altered audit evidence

**Attack:** A user performs an action without audit logging, or an attacker alters an audit record later.

**Impact:** The system cannot reliably prove who accessed or changed a document.

**Mitigation:** Record uploads, downloads, edits, deletions, permission changes, and denied access attempts. Do not expose audit edit/delete functions to normal users. Restrict audit views to administrators.

**Test:** Attempt an unauthorized document request and confirm a denied audit event is created.

**Residual risk:** A database administrator could alter database rows. This challenge project will reduce that risk with application controls and document the limitation honestly.

---

## Threat 8 — Password and secret exposure

**Attack:** Passwords, secret keys, or database credentials are committed to GitHub.

**Impact:** Account takeover and database compromise.

**Mitigation:** Store secrets in `.env`, add `.env` to `.gitignore`, use Django’s password hashing through `set_password()`, and commit only `.env.example`.

**Test:** Check `git status` before every push and confirm `.env` is not included.

## Threat 9 — Permission check missing from a new route

**Attack:** A developer adds a new document route, such as a download, edit, preview, or search route, but forgets to call the central permission function.

**Impact:** A logged-in user could access confidential document content or metadata.

**Mitigation:** Every document route must call `can_access_document()` on the Django server before returning document data. The application must not trust hidden buttons or frontend checks.

**Test:** Tests cover permitted and denied document-detail access. Day 4 will add equivalent tests for download, grant, and revoke routes.

**Residual risk:** Developers must continue using the central function for every new protected route.

---

## Threat 10 — A user grants themselves permission

**Attack:** A viewer attempts to create a permission record that gives themselves `READ` or `EDIT` access to a document.

**Impact:** The viewer gains unauthorised access.

**Mitigation:** Only the document owner can create, change, or revoke document permissions. The model also prevents owners from granting permissions to themselves.

**Test:** A non-owner attempts to create or revoke a permission and must receive `403 Forbidden`.

---

## Threat 11 — Audit records are changed or removed

**Attack:** A normal user attempts to alter or delete an audit event to hide their activity.

**Impact:** The system can no longer reliably show what happened.

**Mitigation:** Audit events have no normal user-facing edit or delete route. In Django admin, audit records are read-only and only administrators can view them.

**Test:** Confirm normal users cannot access the audit dashboard. Confirm Django admin does not offer add, edit, or delete actions for audit events.

**Residual risk:** A person with direct database administration access may still alter records. This limitation is documented and will be strengthened later if time permits.

## Threat 12 — A fake or dangerous file is uploaded with a `.pdf` extension

**Attack:** A user renames a non-PDF file, executable, or malformed content to end in `.pdf` and uploads it.

**Impact:** The platform may store a file that is not the claimed type. Users may download a file that does not open as expected or may be unsafe to open.

**Current mitigation:** TrustVault checks the file extension and maximum file size before saving the upload.

**Known limitation:** Extension validation alone does not prove that the bytes are a valid PDF, DOCX, or TXT file. The automated tests currently use mock bytes with a `.pdf` filename; those files are intentionally not valid PDFs and should not be used for manual PDF-reader testing.

**Planned improvement:** Add MIME-type and file-signature validation where practical, and consider malware scanning in a production deployment.

---

## Threat 13 — Direct file-storage access bypasses the application

**Attack:** A user attempts to use a guessed, saved, or leaked storage path instead of the protected Django download route.

**Impact:** The user could bypass permission checks and download a confidential file.

**Mitigation:** The application does not display `document.file.url`, does not create public media routes, and serves file bytes only through `secure_document_download`, which performs a fresh server-side authorization check.

**Test:** Verify dashboard and document-detail HTML do not include a storage path or media URL. Verify an unauthorized request to the protected download route receives `403 Forbidden`.

**Residual risk:** Production storage must be configured as private. A public cloud-storage bucket would defeat this control.

---

## Threat 14 — Permission revocation does not take effect immediately

**Attack:** A viewer keeps using a prior document link after their permission has been revoked.

**Impact:** A former recipient can continue reading confidential content.

**Mitigation:** The revoke operation sets `revoked_at`. Every subsequent detail and download request checks the currently active permission record through `can_access_document()`.

**Test:** Grant `READ` permission, confirm download succeeds, revoke through the owner-only POST route, then verify the viewer’s next detail and download requests return `403 Forbidden`.

**Residual risk:** A user may retain a file they downloaded before access was revoked. The system cannot delete copies already stored on that user’s device.

## Threat 20 — Production settings or secrets are misconfigured

**Attack:** A deployment starts with debug output enabled, an insecure signing key, wildcard hosts, or a publicly exposed credential.

**Impact:** Error pages may expose implementation details, sessions may be forged, host-header protections may fail, or an attacker may gain access to the database or storage.

**Mitigation:** Production is explicitly selected with `DJANGO_ENV=production`; that mode requires `DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS`, a PostgreSQL `DATABASE_URL`, and private object-storage credentials. HTTPS redirects, secure cookies, HSTS, and proxy HTTPS handling are enabled only in production. Secrets are supplied by the host and excluded from Git.

**Test:** Start settings in a production-configured subprocess and assert debug is disabled, PostgreSQL is selected, allowed hosts are explicit, and HTTPS/cookie protections are active.

**Residual risk:** A wrongly configured provider dashboard, leaked deployment credential, or privileged operator can still undermine these controls. Rotate exposed credentials and restrict access to deployment settings.

## Threat 21 — Public or directly accessible production object storage

**Attack:** A bucket policy or object ACL permits unauthenticated reads, or an application response exposes a permanent object URL.

**Impact:** Anyone who obtains or guesses an object key could bypass Django authorization and download confidential files.

**Mitigation:** Production requires S3-compatible private storage. The backend omits public ACLs, does not use a custom public domain, and refuses to return storage URLs. The protected Django download view checks current authorization before opening the object. Configure the provider to block public policies and ACLs, use a least-privilege bucket-scoped credential, and require TLS.

**Test:** Confirm local and cloud storage backends reject URL generation, no media route exists, and an unauthorized or revoked request is denied before the storage backend opens the object.

**Residual risk:** Provider policy cannot be fully verified by local tests. An administrator must confirm the deployed bucket is private and test public access denial after deployment.

## Threat 22 — Database migration or hosted service failure

**Attack:** A release skips or races schema migrations, loses its database connection, or fails to start while exposing internal error details.

**Impact:** The service may be unavailable or return errors during a release; a misconfigured database could expose user and audit data.

**Mitigation:** The Render blueprint installs declared dependencies, collects static files, runs migrations in its pre-deploy step, and only then starts Gunicorn. Production requires a PostgreSQL URL. Keep backups and do not run migrations concurrently on every scaled web worker.

**Test:** Verify the deployment migration command completes before application start and check the public health endpoint returns only a constant `ok` response.

**Residual risk:** The health endpoint is a liveness check only; it does not test database or storage connectivity. Availability depends on the hosting and database providers.


---

## Threat 15 — Search metadata leakage

**Attack:** A user without access to a document searches for keywords, titles, or owner names and learns that confidential documents exist or infers their metadata.

**Impact:** Unauthorized users can deduce confidential corporate initiatives, M&A targets, employee names, or financial categories through search results or error messages.

**Mitigation:** The search query is constrained at the database level to only documents the requesting user owns or has an active `DocumentPermission` for. Unmatched or unauthorized records are never loaded or revealed in template context.

**Test:** A viewer searches for an owner's private document title or owner username on the dashboard; confirm the document does not appear in search results.

**Residual risk:** None within the application database scope; users can only discover documents they already have authorized access to view.

---

## Threat 16 — Unauthorized audit dashboard access

**Attack:** A document owner, viewer, or unauthenticated user navigates to `/activity/` to inspect system-wide activity, document titles, usernames, and download patterns.

**Impact:** Information disclosure of sensitive system events, access logs, and user activity.

**Mitigation:** The `admin_audit_dashboard` view enforces a strict server-side role check (`request.user.role == "ADMIN"`). It explicitly rejects owners, viewers, and unauthenticated users with `403 Forbidden` or redirection to login. Neither `is_staff` nor `is_superuser` alone can bypass this check.

**Test:** Verify owner and viewer users receive HTTP `403 Forbidden` when requesting `/activity/`. Verify unauthenticated requests redirect to `/login/`.

**Residual risk:** Administrators can see document titles and actor usernames within audit events.

---

## Threat 17 — Audit record modification or deletion

**Attack:** An attacker or malicious insider attempts to modify, falsify, or delete log records to conceal unauthorized activity or cover tracks.

**Impact:** Destruction of audit trail integrity, non-repudiation failure, and inability to investigate security incidents.

**Mitigation:** The `AuditEvent` model has no user-facing edit or delete views. In Django Admin, `has_add_permission`, `has_change_permission`, and `has_delete_permission` are overridden to return `False`, making the log strictly read-only.

**Test:** Automated tests verify `has_add_permission`, `has_change_permission`, and `has_delete_permission` return `False` on the model admin.

**Residual risk:** Direct SQL access to the underlying SQLite database file would allow modification; in production, append-only centralized logging or write-once storage (WORM) should be used.

---

## Threat 18 — Fake files renamed with a `.pdf` extension

**Attack:** An attacker renames a script, executable, HTML, or corrupted file to end in `.pdf` and uploads it to bypass extension-only checks.

**Impact:** The platform stores deceptive files that could exploit recipient PDF reader vulnerabilities, break processing pipelines, or execute unintended content.

**Mitigation:** `DocumentUploadForm.clean_file()` inspects the magic bytes of `.pdf` uploads, requiring the first 5 bytes to match the standard `%PDF-` signature (`b"%PDF-"`). Renamed non-PDF files are rejected with a clear validation error. The file pointer is immediately reset via `uploaded_file.seek(0)`.

**Test:** Upload a text file named `fake.pdf` and verify form validation fails. Upload a file starting with `%PDF-` and verify it succeeds.

**Residual risk & limitations:**
1. **Not Antivirus Scanning:** Magic byte validation checks only header signature consistency; it is NOT antivirus or malware scanning and does not inspect embedded JavaScript or exploit payloads within valid PDF structures.
2. **Limited `.docx` and `.txt` Validation:** `.docx` files are ZIP archives and `.txt` are raw characters; full deep-inspection MIME validation for those formats remains a current limitation.

---

## Threat 19 — Revoked permissions appearing in search results

**Attack:** A user whose permission was recently revoked uses dashboard search filters to see if the document still appears in cached or un-scoped queries.

**Impact:** Former recipients could continue discovering document presence and metadata after access revocation.

**Mitigation:** The dashboard search queryset explicitly filters `permissions__revoked_at__isnull=True`. Revoked permissions are immediately excluded at the database level on every request.

**Test:** Grant permission to a viewer, verify document appears in search, revoke permission via owner POST, and verify document immediately disappears from viewer search results.

**Residual risk:** None; database filtering evaluates live state on every request.


## Threat 15 — Search metadata leakage

**Attack:** A viewer searches for another user’s document and sees its title, owner, category, or date.

**Impact:** Confidential metadata is exposed even if downloading is blocked.

**Mitigation:** The server first limits the queryset to documents owned by the user or shared through an active permission. Search filters are applied only after this authorization scope.

**Test:** A viewer without permission cannot find the owner’s document. A viewer with active permission can find it.

**Residual risk:** Any future search or export endpoint must reuse the same authorization scope.

---

## Threat 16 — Unauthorized audit dashboard access

**Attack:** An owner or viewer opens the audit activity URL directly.

**Impact:** They may learn who accessed confidential documents and when.

**Mitigation:** The dashboard checks the custom `ADMIN` role on the server and returns `403 Forbidden` for other users.

**Test:** Admin receives `200`; owner and viewer receive `403`; logged-out users are redirected to login.

---

## Threat 17 — Audit records are modified or deleted

**Attack:** A user attempts to edit or delete audit events through Django admin.

**Impact:** Evidence of document access or denied attempts could be hidden.

**Mitigation:** Audit events are read-only in Django admin. Add, change, and delete permissions return `False`.

**Test:** Confirm the admin interface provides no edit or delete action for audit events.

---

## Threat 18 — Renamed non-PDF upload

**Attack:** A text file or malicious file is renamed to end with `.pdf`.

**Impact:** Users may download a malformed or unsafe file.

**Mitigation:** PDF uploads must begin with the `%PDF-` file signature in addition to extension and size checks.

**Test:** A text file named `fake.pdf` is rejected.

**Residual risk:** Signature checking does not replace antivirus scanning or complete file-format validation.

---

## Threat 19 — Revoked document appears in search

**Attack:** A user whose permission was revoked searches for the document.

**Impact:** Revoked users may continue discovering confidential metadata.

**Mitigation:** Search includes only permissions where `revoked_at IS NULL`.

**Test:** After revocation, the document disappears from the user’s search results and its detail/download requests return `403 Forbidden`.

## Threat 20 — Production secrets are exposed

**Attack:** A database password, Django secret key, or storage credential is committed to GitHub.

**Impact:** Attackers could take over the application, database, or document storage.

**Mitigation:** Read secrets from environment variables, commit only `.env.example`, and keep `.env` in `.gitignore.

**Test:** Inspect the Git status and repository before pushing. Confirm no `.env` or real credentials are tracked.

---

## Threat 21 — Production runs with debug errors enabled

**Attack:** An attacker triggers an application error while `DEBUG=True`.

**Impact:** Django may reveal settings, file paths, stack traces, or secrets.

**Mitigation:** Set `DEBUG=False` in production and configure `ALLOWED_HOSTS`.

**Test:** Check the deployed settings and trigger a safe invalid request. The response must not expose a Django debug page.

---

## Threat 22 — Public cloud file storage

**Attack:** A storage bucket or object is publicly readable.

**Impact:** Anyone who guesses or obtains an object URL can download confidential documents without Django authorization.

**Mitigation:** Configure private storage and serve files only through the protected Django download view.

**Test:** Attempt direct object access without authentication and confirm it is denied.

**Residual risk:** A cloud-provider bucket policy mistake could bypass application controls, so storage permissions must be reviewed during deployment.

---

## Threat 23 — Incorrect allowed hosts or CSRF configuration

**Attack:** The deployed application accepts unexpected hostnames or rejects/weakens CSRF protection.

**Impact:** Host-header attacks, broken authentication flows, or cross-site request forgery.

**Mitigation:** Configure exact production hosts and trusted HTTPS origins through environment variables.

**Test:** Verify the live hostname works, unexpected hosts are rejected, and POST forms still require CSRF tokens.

---

## Threat 24 — Deployment loses uploaded files

**Attack:** Uploaded documents are stored only on an ephemeral deployment filesystem.

**Impact:** A restart or redeploy deletes documents or makes them unavailable.

**Mitigation:** Use a persistent private object-storage service for production uploads. Keep local filesystem storage only for development.

**Test:** Upload a document, redeploy or restart the service, then verify the authorized owner can still download it.