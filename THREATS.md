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