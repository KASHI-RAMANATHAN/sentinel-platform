"""
app/firebase/firestore_client.py

Firestore client accessor.

Exposes a single `get_firestore_client` dependency that the services
layer uses to talk to Firestore. Keeping this isolated makes it trivial
to mock Firestore in unit tests (override the dependency) without
touching business logic.
"""

import logging

from firebase_admin import firestore
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.firebase.firebase import init_firebase_app

logger = logging.getLogger(__name__)

_firestore_client: FirestoreClient | None = None


def get_firestore_client() -> FirestoreClient:
    """
    Returns a cached Firestore client instance.

    FastAPI dependency usage:
        db: FirestoreClient = Depends(get_firestore_client)

    TODO: Add connection health checks / retry policy for production.
    """
    global _firestore_client

    if _firestore_client is None:
        init_firebase_app()
        _firestore_client = firestore.client()
        logger.info("Firestore client created.")

    return _firestore_client
