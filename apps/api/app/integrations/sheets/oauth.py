import base64
from datetime import timedelta
import hashlib
import json
import os
import secrets
from pathlib import Path
from urllib.parse import urlencode

import httpx
from sqlalchemy import delete, select

from app.core.encryption import decrypt, encrypt
from app.db.models import OAuthCredential, OAuthState, now
from app.schemas import as_utc
from app.services.errors import NeedsInput

SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
WRITE_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def write_enabled(spreadsheet_id):
    from app.integrations.sheets.client import LIVE_SHEET_ID
    return bool(spreadsheet_id and spreadsheet_id != LIVE_SHEET_ID and os.environ.get("SHEETS_WRITE_COPY_ID") == spreadsheet_id)


def requested_scope():
    return WRITE_SCOPE if write_enabled(os.environ.get("SHEETS_WRITE_COPY_ID")) else SCOPE


def valid_scope(scope):
    scopes = set(scope.split())
    return scopes == {SCOPE} or (requested_scope() == WRITE_SCOPE and WRITE_SCOPE in scopes and scopes <= {SCOPE, WRITE_SCOPE})
REDIRECT = "http://127.0.0.1:8000/oauth/google/callback"


def client_settings():
    id = os.environ.get("GOOGLE_CLIENT_ID", "")
    secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not id or not secret:
        from app.core.config import ROOT
        file = Path(os.environ.get("GOOGLE_OAUTH_CLIENT_FILE", ROOT / ".local/google-oauth-client.json")).expanduser()
        try:
            config = json.loads(file.read_text())["web"]
            id, secret = config["client_id"], config["client_secret"]
            if not isinstance(id, str) or not isinstance(secret, str) or not id or not secret or REDIRECT not in config.get("redirect_uris", []):
                raise ValueError("Invalid OAuth client")
        except (OSError, ValueError, KeyError, TypeError):
            raise NeedsInput("Place the Google Web OAuth client JSON in .local/google-oauth-client.json, with the documented loopback redirect URI.") from None
    return id, secret


def start(session):
    client_id, _ = client_settings()
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    session.execute(delete(OAuthState).where(OAuthState.expires_at < now()))
    session.add(OAuthState(digest=hashlib.sha256(state.encode()).hexdigest(), encrypted_verifier=encrypt(verifier), expires_at=now() + timedelta(minutes=10)))
    session.commit()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
        "client_id": client_id, "redirect_uri": REDIRECT, "response_type": "code", "scope": requested_scope(),
        "access_type": "offline", "prompt": "consent", "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })


def token_request(data, client=None):
    owned = client is None
    client = client or httpx.Client(timeout=30)
    try:
        response = client.post("https://oauth2.googleapis.com/token", data=data)
        response.raise_for_status()
        result = response.json()
        if not isinstance(result.get("access_token"), str):
            raise ValueError("No access token")
        if not valid_scope(result.get("scope", "")):
            raise ValueError("Unexpected permissions")
        return result
    except (httpx.HTTPError, ValueError, TypeError):
        raise NeedsInput("Google OAuth failed. Check client settings and grant only the configured spreadsheet permission (read-only by default).") from None
    finally:
        if owned:
            client.close()


def finish(session, state, code, client=None):
    digest = hashlib.sha256(state.encode()).hexdigest()
    pending = session.get(OAuthState, digest)
    if not pending or as_utc(pending.expires_at) < now():
        raise NeedsInput("OAuth state is invalid or expired. Start the connection again.")
    verifier = decrypt(pending.encrypted_verifier)
    # Consume state atomically before exchanging the code; concurrent replays fail.
    consumed = session.execute(delete(OAuthState).where(OAuthState.digest == digest))
    session.commit()
    if consumed.rowcount != 1:
        raise NeedsInput("OAuth state was already used. Start the connection again.")
    id, secret = client_settings()
    tokens = token_request({"client_id": id, "client_secret": secret, "code": code, "grant_type": "authorization_code", "redirect_uri": REDIRECT, "code_verifier": verifier}, client)
    if not tokens.get("refresh_token"):
        raise NeedsInput("Google did not grant offline access. Reconnect with consent to allow refresh tokens.")
    save_tokens(session, tokens)


def save_tokens(session, tokens):
    tokens = {**tokens, "expires_at": (now() + timedelta(seconds=int(tokens.get("expires_in", 3600)) - 60)).isoformat()}
    row = session.get(OAuthCredential, "google") or OAuthCredential(id="google")
    row.ciphertext = encrypt(json.dumps(tokens))
    session.add(row)
    session.commit()


def access_token(session, client=None, require_write=False):
    from datetime import datetime
    row = session.get(OAuthCredential, "google")
    if not row:
        raise NeedsInput("Connect Google before running Sheet import or sync.")
    tokens = json.loads(decrypt(row.ciphertext))
    if not valid_scope(tokens.get("scope", "")):
        raise NeedsInput("Reconnect Google with read-only spreadsheet permission. Broader stored grants are not used.")
    if datetime.fromisoformat(tokens["expires_at"]) <= now():
        id, secret = client_settings()
        refreshed = token_request({"client_id": id, "client_secret": secret, "refresh_token": tokens["refresh_token"], "grant_type": "refresh_token"}, client)
        tokens = {**tokens, **refreshed}
        save_tokens(session, tokens)
    if require_write and WRITE_SCOPE not in set(tokens.get("scope", "").split()):
        raise NeedsInput("Reconnect Google to grant the approved development-copy write permission.")
    return tokens["access_token"]
