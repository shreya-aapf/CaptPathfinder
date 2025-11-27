"""
Helper utilities for CaptPathfinder.
"""

import hashlib
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def generate_idempotency_key(
    event_id: Optional[str],
    user_id: str,
    profile_field: str,
    value: str
) -> str:
    """
    Generate idempotency key for deduplicating events.
    
    Uses SHA256 hash of event components.
    """
    components = [
        event_id or "",
        user_id,
        profile_field,
        value
    ]
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()


def format_date_range(start: datetime, end: datetime) -> str:
    """Format date range for display."""
    return f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}"


def get_profile_url(user_id: str, base_url: Optional[str] = None) -> str:
    """
    Generate profile URL for a user.
    
    This would be customized based on your community platform's URL structure.
    """
    if base_url:
        return f"{base_url}/profile/{user_id}"
    return f"https://community.example.com/profile/{user_id}"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    # Remove or replace dangerous characters
    sanitized = filename.replace("/", "_").replace("\\", "_")
    sanitized = "".join(c for c in sanitized if c.isalnum() or c in "._-")
    return sanitized

