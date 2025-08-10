"""Authentication module for Google OAuth integration."""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

SCOPES = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

CLIENT_SECRETS = 'client_secret.json'  # Download this from Google Cloud Console
TOKEN_STORE = os.path.expanduser('~/.slywriter_tokens.json')


def sign_in_with_google():
    """
    Launches browser for OAuth, saves token, and returns user info.
    """
    creds = None
    if os.path.exists(TOKEN_STORE):
        creds = Credentials.from_authorized_user_file(TOKEN_STORE, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_STORE, 'w') as f:
            f.write(creds.to_json())

    # Extract user info
    from googleapiclient.discovery import build
    service = build('oauth2', 'v2', credentials=creds)
    info = service.userinfo().get().execute()
    return {
        'id': info['id'],
        'email': info['email'],
        'name': info.get('name', ''),
        'picture': info.get('picture', ''),
        'token': creds.to_json()
    }


def get_saved_user():
    """
    Loads saved credentials if still valid and returns user info.
    """
    if os.path.exists(TOKEN_STORE):
        creds = Credentials.from_authorized_user_file(TOKEN_STORE, SCOPES)
        if creds and creds.valid:
            from googleapiclient.discovery import build
            service = build('oauth2', 'v2', credentials=creds)
            info = service.userinfo().get().execute()
            return {
                'id': info['id'],
                'email': info['email'],
                'name': info.get('name', ''),
                'picture': info.get('picture', ''),
                'token': creds.to_json()
            }
    return None


def save_user(user_info):
    """Save user credentials to token store."""
    if user_info and 'token' in user_info:
        with open(TOKEN_STORE, 'w') as f:
            f.write(user_info['token'])


def logout_user():
    """Deletes local token store."""
    if os.path.exists(TOKEN_STORE):
        os.remove(TOKEN_STORE)


# Backward compatibility aliases
sign_out = logout_user