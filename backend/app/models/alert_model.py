"""
app/models/alert_model.py

Internal domain model for an anomaly alert record.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AlertRecord:
    """Internal representation of a stored alert document."""

    user_id: str
    title: str
    severity: str
    status: str
    description: Optional[str] = None
    risk_score: Optional[float] = None
    attack_type: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None  # Firestore document ID

    def to_firestore_dict(self) -> Dict[str, Any]:
        """
        TODO: Implement mapping to a Firestore-compatible dict once
        the alerts collection schema is finalized.
        """
        raise NotImplementedError("Firestore serialization not yet implemented.")
