# Google OAuth Setup (Quick)

1. Go to https://console.cloud.google.com/ and create a project (or use an existing one).
2. Enable the Gmail API for the project.
3. Create OAuth 2.0 Client ID credentials (Application type: Desktop app).
4. Download the `credentials.json` file and save it somewhere safe. Put its path into the `GOOGLE_OAUTH_CREDENTIALS` environment variable or `.env`.
5. Run `python email_fetcher.py --init-auth` in the repo to complete the installed app OAuth flow. The script will store tokens using `keyring` (or encrypted file fallback).

Minimum Gmail scope used in example: `https://www.googleapis.com/auth/gmail.readonly`.

Important: request only the scopes you need when building your real app.
