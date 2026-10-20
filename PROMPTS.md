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