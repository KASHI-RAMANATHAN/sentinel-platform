"""
app/utils/time_utils.py

Shared time/date helper utilities used across services.
"""

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    """Returns the current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def minutes_ago(minutes: int) -> datetime:
    """Returns a UTC timestamp `minutes` minutes before now — useful
    for building 'recent window' Firestore query cutoffs."""
    return utc_now() - timedelta(minutes=minutes)
