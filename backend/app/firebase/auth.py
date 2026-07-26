"""
app/firebase/auth.py

Firebase Authentication helper (PLACEHOLDER ONLY).

This module will eventually verify Firebase ID tokens sent by the
frontend and expose the decoded user as a FastAPI dependency
(e.g. Depends(get_current_user)) so routes can be protected.

Not wired into any routes yet — hackathon scope currently ships all
endpoints open/unauthenticated.
"""

import logging
from typing import Optional

from fastapi import Header, HTTPException, status
from firebase_admin import auth as firebase_auth

from app.core.config import settings

logger = logging.getLogger(__name__)


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> Optional[dict]:
    """
    PLACEHOLDER dependency for verifying a Firebase ID token.

    TODO:
    - Extract Bearer token from the Authorization header.
    - Call firebase_auth.verify_id_token(token).
    - Return the decoded token / user claims.
    - Raise HTTPException(401) on invalid/expired tokens.

    Currently a no-op that returns None when auth is disabled, so
    routes can call this dependency without breaking the hackathon
    build before real auth is implemented.
    """
    if not settings.FIREBASE_AUTH_ENABLED:
        return None

    # TODO: implement real token verification, e.g.:
    # if not authorization or not authorization.startswith("Bearer "):
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    # token = authorization.split(" ")[1]
    # decoded_token = firebase_auth.verify_id_token(token)
    # return decoded_token

    raise NotImplementedError("Firebase Authentication is not yet implemented.")
