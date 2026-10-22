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
