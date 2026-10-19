# TrustVault

TrustVault is a secure document-sharing platform built for the SnovaSys Fresher Hiring Challenge 2026.

The system is designed so that only authorised users can access a document, and important document activity can be traced through an audit trail.

## Features

- User authentication: login and logout
- Three user roles:
  - Administrator
  - Document Owner
  - Viewer
- Secure document upload and management
- Per-document permissions for named users
- Read and edit permissions
- Owners can grant and revoke access
- Search documents by name, owner, category, and date
- Audit log for uploads, downloads, updates, deletions, permission changes, and denied access attempts
- Admin dashboard for document activity and permission changes
- Automated tests proving one user cannot access another user's private document

## Security Model

TrustVault enforces access rules on the server for every document request.

A user can access a document only when:

1. They are the document owner, or
2. They have an active explicit permission grant for that document.

Users without permission cannot view, download, edit, delete, or discover documents through search.

When an owner revokes access, the user loses access immediately on their next request.

Uploaded files are not public. Every download goes through a Django view that checks permission before sending the file.

## Technology Stack

- Python
- Django
- SQLite for local development
- PostgreSQL for production deployment
- Django ORM
- Django built-in authentication
- HTML, CSS, Bootstrap
- Pytest and pytest-django for testing
- Git and GitHub for version control

## Project Structure

```text
trustvault/
├── accounts/          # User accounts, authentication, and roles
├── documents/         # Documents, uploads, permissions, and downloads
├── audit/             # Audit logs and administrator activity view
├── templates/         # HTML templates
├── tests/             # Automated tests
├── trustvault/        # Django settings and URLs
├── README.md
├── THREATS.md
├── PROMPTS.md
├── requirements.txt
└── manage.py
```

## Local Setup

1. Clone the repository.

```bash
git clone https://github.com/YOUR-USERNAME/trustvault.git
cd trustvault
```

2. Create and activate a virtual environment.

```powershell
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Run database migrations.

```bash
python manage.py migrate
```

5. Create sample users or a superuser.

```bash
python manage.py createsuperuser
```

6. Start the development server.

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in the browser.

## Testing

Run automated tests with:

```bash
pytest
```

Security tests include checks that an unauthorised user cannot access or download another user’s document.

## API Access Rules

| Action | Allowed users |
|---|---|
| Upload document | Authenticated document owner |
| View/download document | Owner or explicitly granted user |
| Edit document | Owner or user with edit permission |
| Delete document | Owner only |
| Grant/revoke permission | Owner only |
| View audit dashboard | Administrator only |

## Documentation

- `THREATS.md` explains security risks, mitigations, and related tests.
- `PROMPTS.md` records how AI was used during development, including mistakes found and corrections made.
- The repository commit history shows development progress across the challenge week.

## Known Limitations

This is a challenge project. Any unfinished features, accepted risks, and future improvements will be documented clearly before submission.
