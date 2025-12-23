# email_fetcher.py
"""
Simple Gmail fetcher using google-auth-oauthlib and google-api-python-client.
Supports an --init-auth mode to run the OAuth installed-app flow once and persist tokens.
"""
import argparse
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from storage import TokenStore
from utils import get_credentials_path

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

TOKEN_KEY = os.getenv('OAUTH_TOKEN_KEY', 'local_agent_gmail_token')
store = TokenStore(TOKEN_KEY)

def init_auth():
    cred_path = get_credentials_path()
    if not cred_path:
        raise RuntimeError('Set GOOGLE_OAUTH_CREDENTIALS env var to your credentials.json path')
    flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
    creds = flow.run_local_server(port=0)
    # Save tokens to token store
    store.set({
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'scopes': list(creds.scopes) if creds.scopes else [],
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
    })
    print('Stored tokens in secure store (keyring or fallback file).')

def load_creds():
    token_data = store.get(fallback_password=None)  # For keyring, no password required
    if not token_data:
        return None
    creds = Credentials(
        token=token_data.get('token'),
        refresh_token=token_data.get('refresh_token'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=token_data.get('client_id'),
        client_secret=token_data.get('client_secret'),
        scopes=token_data.get('scopes')
    )
    # Note: google-auth will auto-refresh if expired when used with an authorized session.
    return creds

def fetch_recent_messages(max_results=10):
    creds = load_creds()
    if not creds:
        raise RuntimeError('No creds found. Run with --init-auth first to authenticate.')
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=max_results).execute()
    messages = results.get('messages', [])
    out = []
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')
        snippet = msg.get('snippet')
        out.append({'id': m['id'], 'subject': subject, 'snippet': snippet})
    return out

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init-auth', action='store_true', help='Run OAuth flow and store tokens')
    args = parser.parse_args()
    if args.init_auth:
        init_auth()
    else:
        msgs = fetch_recent_messages(5)
        for m in msgs:
            print(f"- {m['subject']}: {m['snippet']}")
