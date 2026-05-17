# Security Policy

## Secrets

Never commit Google OAuth client JSON files, refresh tokens, access tokens, `.env` files, or browser-exported credentials.

The CLI stores local auth material outside this repository by default:

```text
~/.codex/google-calendar-api-direct/client_secret.json
~/.codex/google-calendar-api-direct/token.json
```

If a credential is accidentally committed, revoke it in Google Cloud Console and rotate the local OAuth client before continuing.

## Reporting

Open a private security advisory or contact the repository owner privately for credential exposure or authorization issues.
