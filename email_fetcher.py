# email_fetcher.py
"""
Simple Gmail fetcher using google-auth-oauthlib and google-api-python-client.

Supports:
- `--init-auth` mode to run the OAuth installed-app flow once and persist tokens.
- `fetch_recent_messages(max_results=10)` to retrieve recent email metadata.

Gmail scope: readonly by default.
"""
import argparse
import os
from typing import List, Dict, Any

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from storage import TokenStore
from utils import get_credentials_path, env

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

TOKEN_KEY = env("OAUTH_TOKEN_KEY", "local_agent_gmail_token")
store = TokenStore(TOKEN_KEY)


def init_auth() -> None:
    """Run the OAuth flow and store tokens securely."""
    cred_path = get_credentials_path()
    if not cred_path:
        raise RuntimeError(
            "Set GOOGLE_OAUTH_CREDENTIALS env var to your credentials.json path"
        )

    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save tokens to token store
    store.set(
        {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "scopes": creds.scopes,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
        }
    )
    print("✅ Stored tokens in secure store (keyring or fallback file).")


def load_creds() -> Credentials | None:
    """Load credentials from secure storage."""
    token_data = store.get(fallback_password=None)  # With keyring, no password needed
    if not token_data:
        return None

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )
    return creds


def fetch_recent_messages(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch the most recent messages from Gmail.

    Returns a list of:
    {
      "id": "<message id>",
      "subject": "<subject or (no subject)>",
      "snippet": "<gmail snippet>"
    }
    """
    creds = load_creds()
    if not creds:
        raise RuntimeError("No creds found. Run with --init-auth first to authenticate.")

    service = build("gmail", "v1", credentials=creds)
    results = (
        service.users()
        .messages()
        .list(userId="me", maxResults=max_results)
        .execute()
    )
    messages = results.get("messages", [])
    out: List[Dict[str, Any]] = []

    for m in messages:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=m["id"], format="full")
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        subject = next(
            (h["value"] for h in headers if h.get("name") == "Subject"), "(no subject)"
        )
        snippet = msg.get("snippet") or ""
        out.append({"id": m["id"], "subject": subject, "snippet": snippet})

    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--init-auth", action="store_true", help="Run OAuth flow and store tokens"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=5,
        help="Number of recent emails to print (when not using --init-auth)",
    )
    args = parser.parse_args()

    if args.init_auth:
        init_auth()
    else:
        msgs = fetch_recent_messages(args.max_results)
        for m in msgs:
            print(f"- {m['subject']}: {m['snippet']}")
