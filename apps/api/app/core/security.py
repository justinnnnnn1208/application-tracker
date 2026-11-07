import secrets

from fastapi import HTTPException, Request
from fastapi.security.utils import get_authorization_scheme_param


def require_access(request: Request):
    scheme, token = get_authorization_scheme_param(request.headers.get("Authorization"))
    if scheme.lower() != "bearer" or not secrets.compare_digest(
        token.encode(), request.app.state.settings.access_token.encode()
    ):
        raise HTTPException(401, "A valid local access token is required", headers={"WWW-Authenticate": "Bearer"})
