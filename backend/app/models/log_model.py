"""
app/models/log_model.py

Internal domain model for a behavioral log record.

Distinct from app/schemas/log_schema.py: schemas define the API
request/response contract, while this module represents the internal
shape of a log document as stored in / read from Firestore. Keeping
these separate lets the storage representation evolve independently
of the public API contract.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class LogRecord:
    """Internal representation of a stored log entry."""

    user_id: str
    source: str
    action: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None  # Firestore document ID, set after persistence

    def to_firestore_dict(self) -> Dict[str, Any]:
        """
        Converts this record into a plain dict suitable for
        Firestore's `collection.add(...)` / `document.set(...)`.

        TODO: Implement actual field mapping once Firestore schema
        for logs is finalized.
        """
        raise NotImplementedError("Firestore serialization not yet implemented.")
