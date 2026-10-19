# Threat Model

## Unauthorized document access

Risk: A user tries to open another user's document by changing its ID in the URL.

Mitigation: Every document view and download checks permissions on the Django server.

Test: A viewer trying to download an owner's private document receives a 403 Forbidden response.

## Access after revocation

Risk: A user continues using an old download link after access is removed.

Mitigation: The server checks active permissions on every download request.

Test: After permission is revoked, the same download request returns 403.

## Public file URLs

Risk: Uploaded files are publicly accessible through a media URL.

Mitigation: Files are private and served only through an authorised Django download view.