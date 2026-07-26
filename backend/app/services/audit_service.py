"""
app/services/audit_service.py

Service layer for writing Audit Logs to Firestore.
"""
import logging
import asyncio
from app.schemas.audit_schema import AuditLogCreate, AuditLog
from app.firebase.firestore_client import get_firestore_client

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self):
        self._db = None

    @property
    def db(self):
        if not self._db:
            try:
                self._db = get_firestore_client()
            except Exception as e:
                logger.error(f"Could not get firestore client for AuditService: {e}")
        return self._db

    def log_event_sync(self, event: AuditLogCreate):
        """
        Synchronously write an audit log to Firestore.
        Prefer log_event for async contexts.
        """
        try:
            if not self.db:
                logger.warning("Firestore client not available. Skipping audit log.")
                return
            
            audit_log = AuditLog.generate(event)
            doc_ref = self.db.collection('audit_logs').document(audit_log.log_id)
            doc_ref.set(audit_log.model_dump())
            logger.debug(f"Audit log created: {audit_log.action} by {audit_log.actor}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    async def log_event(self, event: AuditLogCreate):
        """
        Asynchronously write an audit log to Firestore.
        Uses asyncio.to_thread to prevent blocking the event loop.
        """
        await asyncio.to_thread(self.log_event_sync, event)

audit_service = AuditService()
