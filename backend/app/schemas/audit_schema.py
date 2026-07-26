"""
app/schemas/audit_schema.py

Schema for the Audit Log module.
"""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum
import uuid

class AuditActor(str, Enum):
    SYSTEM = "System"
    SOC_ANALYST = "SOC Analyst"
    BACKEND = "Backend"
    ML_ENGINE = "ML Engine"
    FIREBASE = "Firebase"

class AuditCategory(str, Enum):
    SYSTEM = "System"
    SECURITY = "Security"
    ANALYST = "Analyst"
    ERRORS = "Errors"

class AuditStatus(str, Enum):
    SUCCESS = "Success"
    WARNING = "Warning"
    CRITICAL = "Critical"
    FAILED = "Failed"

class AuditLogCreate(BaseModel):
    actor: AuditActor
    action: str
    category: AuditCategory
    resource: str
    status: AuditStatus
    details: str
    alert_id: Optional[str] = None
    entity_id: Optional[str] = None

class AuditLog(AuditLogCreate):
    log_id: str
    timestamp: str

    @classmethod
    def generate(cls, data: AuditLogCreate) -> "AuditLog":
        return cls(
            **data.model_dump(),
            log_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat()
        )
