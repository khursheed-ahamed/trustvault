# TrustVault routes

These routes currently return Django-rendered HTML pages or a streamed file; they are not a JSON API. Form POSTs require Django CSRF protection. Authorization is performed on the server for every protected route. Hiding a link, knowing a document ID, or knowing an object key does not grant access.

For protected routes, unauthenticated requests are redirected to the login page. A signed-in user who lacks the required role or permission receives `403 Forbidden`. Unknown document or permission IDs return `404 Not Found`.

## Application routes

| Method | URL | Authentication | Allowed role/permission | Success response | Denied response and security behavior |
|---|---|---|---|---|---|
| GET | `/health/` | Not required | Any client | `200 OK`, plain-text body `ok`; no database or user data is returned. | No authentication denial. This is a liveness check only; it does not prove database or object storage availability. |
| GET | `/` | Required | Any authenticated role | `200 OK`, document dashboard with only owned or actively shared documents. | Login redirect if anonymous. Search filters run only after the authorized queryset is scoped. |
| GET | `/documents/` | Required | Any authenticated role | Same dashboard/search behavior as `/`. | Login redirect if anonymous; unauthorized document metadata is excluded from the queryset. |
| GET, POST | `/signup/`; `/accounts/signup/` | Not required | New user; role defaults to `VIEWER` | GET renders the signup form; valid POST creates the account, logs it in, and redirects to `/`. | Invalid POST returns the form with errors. CSRF middleware protects POST. |
| GET, POST | `/login/`; `/accounts/login/` | Not required | Any existing account | GET renders login form; valid POST establishes a session and redirects to the configured destination. | Invalid credentials return the login form with an error. CSRF middleware protects POST. |
| POST | `/logout/`; `/accounts/logout/` | Session recommended | Any signed-in user | Ends the session and redirects to the login page. | GET receives `405 Method Not Allowed`; an anonymous POST is safely handled by Django's logout view. CSRF middleware protects POST. |
| GET | `/documents/upload/` | Required | User with role `OWNER` | `200 OK`, upload form. | Non-owner gets `403`; anonymous user is redirected to login. |
| POST | `/documents/upload/` | Required | User with role `OWNER` | Valid upload is saved, an upload audit event is recorded, and the response redirects to that document's detail page. | Non-owner gets `403`. Invalid file or form returns the form with errors. Allowed extensions, 10 MB size limit, and PDF signature checks are enforced server-side. |
| GET | `/documents/<document_id>/` | Required | Document owner or user with active `READ` or `EDIT` permission | `200 OK`, document detail and metadata; a view audit event is recorded. | Unauthorized users get `403` and an `ACCESS_DENIED` audit event. Every request rechecks current permission; revoked grants fail immediately. |
| GET | `/documents/<document_id>/download/` | Required | Document owner or user with active `READ` or `EDIT` permission | `200 OK`, file bytes streamed by Django with an attachment disposition; a download audit event is recorded. | Unauthorized users get `403` and an `ACCESS_DENIED` audit event. Authorization is checked before the file is opened. No public or permanent object URL is returned. |
| GET, POST | `/documents/<document_id>/permissions/` | Required | That document's owner only | GET displays grants; valid POST creates or updates a `READ`/`EDIT` grant, records an audit event, and redirects back to the page. | Non-owner gets `403` and a denied audit event. CSRF middleware protects POST. |
| POST | `/documents/<document_id>/permissions/<permission_id>/revoke/` | Required | That document's owner only | Revokes the grant immediately, records a revocation audit event, and redirects to the permission page. | Non-owner gets `403` and a denied audit event; GET receives `405 Method Not Allowed`. CSRF middleware protects POST. Detail, download, and search requests use the current permission state. |
| GET | `/activity/` | Required | Custom role `ADMIN` only | `200 OK`, filtered audit dashboard. | Anonymous users are redirected to login. Owners and viewers receive `403`, even if they are Django staff or superusers without the `ADMIN` role. |
| GET | `/admin/` and Django admin descendants | Required | Django staff account with the relevant Django admin permission | Django admin pages according to built-in model permissions. Audit events are read-only. | Anonymous users are redirected to admin login; accounts without permissions are denied by Django admin. Custom `ADMIN` application role alone does not grant Django admin permissions. |

## Search parameters

The GET dashboard accepts `q` (title), `owner` (owner username), `category`, `uploaded_from`, and `uploaded_to` (`YYYY-MM-DD`). Search filters never widen the authorized queryset. Invalid dates produce an empty result page with form errors rather than an unscoped query.

## Storage and audit guarantees

The application does not configure a public media route or expose `document.file.url`. Production files use private S3-compatible storage; access is streamed through the protected download route after the current server-side permission check. Audit records are append-only through the model and ORM manager, referenced users/documents cannot be deleted while audit events refer to them, and audit add/change/delete is disabled in Django admin. Direct database-owner access remains outside application-level protection.
