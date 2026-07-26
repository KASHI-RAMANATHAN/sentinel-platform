"""
app/firebase/firebase.py

Firebase Admin SDK bootstrap.

Responsible ONLY for initializing the Firebase Admin app from the
service account credentials referenced in the environment. Firestore
client access and Auth helpers live in their own modules
(firestore_client.py, auth.py) and depend on this module having run
initialization first.
"""

import logging

import firebase_admin
from firebase_admin import credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app: firebase_admin.App | None = None


def init_firebase_app() -> firebase_admin.App:
    """
    Initializes (once) and returns the Firebase Admin App instance.

    Uses the service account JSON path configured via
    FIREBASE_SERVICE_ACCOUNT_PATH in the environment / .env file.

    Safe to call multiple times — subsequent calls return the existing
    initialized app rather than re-initializing.
    """
    global _firebase_app

    if _firebase_app is not None:
        return _firebase_app

    if not firebase_admin._apps:
        # TODO: Add error handling for missing/invalid service account file.
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        _firebase_app = firebase_admin.initialize_app(
            cred,
            {"projectId": settings.FIREBASE_PROJECT_ID} if settings.FIREBASE_PROJECT_ID else None,
        )
        logger.info("Firebase Admin SDK initialized.")
    else:
        _firebase_app = firebase_admin.get_app()

    return _firebase_app


def get_firebase_app() -> firebase_admin.App:
    """
    FastAPI-dependency-friendly accessor for the initialized Firebase app.
    """
    return init_firebase_app()
