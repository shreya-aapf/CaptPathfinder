"""
Event Processor Service
========================
Handles processing of webhook events from the community platform.
Classifies job titles and updates user state accordingly.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
import httpx

from ..models import WebhookEvent, UserMetadata
from ..database import get_db
from ..classification import classify_title, get_classifier
from ..utils.helpers import generate_idempotency_key
from ..config import get_settings

logger = logging.getLogger(__name__)


class EventProcessor:
    """Processes webhook events and manages user state."""
    
    def __init__(self):
        """Initialize event processor."""
        self.db = get_db()
        self.classifier = get_classifier()
        self.settings = get_settings()
    
    async def fetch_user_metadata(self, user_id: str) -> Optional[UserMetadata]:
        """
        Fetch additional user metadata from community API.
        
        This is a stub that should be implemented to call your actual
        community platform API.
        """
        if not self.settings.community_api_url:
            logger.warning("Community API URL not configured, using defaults")
            return UserMetadata(
                user_id=user_id,
                country=None,
                company=None,
                joined_at=datetime.now()  # Fallback
            )
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.settings.community_api_url}/users/{user_id}",
                    headers={
                        "Authorization": f"Bearer {self.settings.community_api_key}"
                    },
                    timeout=5.0
                )
                response.raise_for_status()
                data = response.json()
                
                return UserMetadata(
                    user_id=user_id,
                    country=data.get('country'),
                    company=data.get('company'),
                    joined_at=data.get('joined_at')
                )
        except Exception as e:
            logger.error(f"Failed to fetch user metadata for {user_id}: {e}")
            # Return minimal metadata
            return UserMetadata(user_id=user_id, joined_at=datetime.now())
    
    def store_raw_event(
        self,
        event: WebhookEvent,
        idempotency_key: str
    ) -> Optional[int]:
        """
        Store raw event in events_raw table.
        
        Returns event ID if inserted, None if duplicate.
        """
        with self.db.get_cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO events_raw (
                        event_id, user_id, username, profile_field,
                        value, old_value, idempotency_key, processed
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, FALSE)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING id
                """, (
                    None,  # event_id
                    event.userId,
                    event.username,
                    event.profileField,
                    event.value,
                    event.oldValue,
                    idempotency_key
                ))
                
                result = cur.fetchone()
                if result:
                    event_id = result['id']
                    logger.info(f"Stored raw event {event_id} for user {event.userId}")
                    return event_id
                else:
                    logger.info(f"Duplicate event for user {event.userId}, skipping")
                    return None
            except Exception as e:
                logger.error(f"Error storing raw event: {e}")
                raise
    
    def process_classification(
        self,
        user_id: str,
        username: str,
        title: str,
        country: Optional[str],
        company: Optional[str],
        joined_at: Optional[datetime]
    ) -> Tuple[bool, str]:
        """
        Process title classification and update user state.
        
        Returns: (is_senior, seniority_level)
        """
        # Classify the title
        is_senior, seniority_level = classify_title(title)
        
        with self.db.transaction() as cur:
            if not is_senior:
                # User is NOT senior - remove from user_state if exists
                cur.execute("""
                    DELETE FROM user_state WHERE user_id = %s
                """, (user_id,))
                
                deleted = cur.rowcount
                if deleted > 0:
                    logger.info(f"Removed non-senior user {user_id} from user_state")
                
                return (False, "")
            
            # User IS senior - check if they exist in user_state
            cur.execute("""
                SELECT user_id, seniority_level, first_detected_at
                FROM user_state
                WHERE user_id = %s
            """, (user_id,))
            
            existing = cur.fetchone()
            
            if not existing:
                # First time detection - insert into user_state and detections
                cur.execute("""
                    INSERT INTO user_state (
                        user_id, username, title, seniority_level,
                        country, company, joined_at,
                        first_detected_at, last_seen_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                """, (
                    user_id, username, title, seniority_level,
                    country, company, joined_at
                ))
                
                # Insert detection record
                cur.execute("""
                    INSERT INTO detections (
                        user_id, username, title, seniority_level,
                        country, company, joined_at, detected_at, rules_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                """, (
                    user_id, username, title, seniority_level,
                    country, company, joined_at,
                    self.classifier.version
                ))
                
                logger.info(
                    f"First detection: User {user_id} classified as {seniority_level}"
                )
            else:
                # Existing senior user - update state
                old_level = existing['seniority_level']
                
                cur.execute("""
                    UPDATE user_state
                    SET username = %s,
                        title = %s,
                        seniority_level = %s,
                        country = %s,
                        company = %s,
                        last_seen_at = NOW()
                    WHERE user_id = %s
                """, (
                    username, title, seniority_level,
                    country, company, user_id
                ))
                
                # Check if this is a "promotion" from VP to C-suite
                if old_level == 'vp' and seniority_level == 'csuite':
                    # Insert promotion detection
                    cur.execute("""
                        INSERT INTO detections (
                            user_id, username, title, seniority_level,
                            country, company, joined_at, detected_at, rules_version
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """, (
                        user_id, username, title, seniority_level,
                        country, company, joined_at,
                        self.classifier.version
                    ))
                    logger.info(
                        f"Promotion detected: User {user_id} from {old_level} to {seniority_level}"
                    )
                else:
                    logger.info(
                        f"Updated existing senior user {user_id} with level {seniority_level}"
                    )
        
        return (is_senior, seniority_level)
    
    async def process_event(self, event: WebhookEvent) -> dict:
        """
        Process a webhook event end-to-end.
        
        Returns processing result summary.
        """
        # Generate idempotency key
        idempotency_key = generate_idempotency_key(
            None,  # event_id if available
            event.userId,
            event.profileField,
            event.value
        )
        
        # Check if this is a Job Title update
        is_job_title = event.profileField.lower() == "job title"
        
        if not is_job_title:
            # Not a job title update - store minimally and mark as processed
            logger.debug(
                f"Event for {event.userId} is not Job Title, field: {event.profileField}"
            )
            # Optionally store for audit
            # self.store_raw_event(event, idempotency_key)
            return {
                "status": "skipped",
                "reason": "not_job_title",
                "user_id": event.userId
            }
        
        # Store raw event
        event_id = self.store_raw_event(event, idempotency_key)
        if event_id is None:
            return {
                "status": "duplicate",
                "user_id": event.userId
            }
        
        # Fetch user metadata (if not already in webhook)
        if not event.country or not event.company or not event.joined_at:
            metadata = await self.fetch_user_metadata(event.userId)
            event.country = event.country or metadata.country
            event.company = event.company or metadata.company
            event.joined_at = event.joined_at or metadata.joined_at
        
        # Process classification and update state
        is_senior, seniority_level = self.process_classification(
            user_id=event.userId,
            username=event.username,
            title=event.value,
            country=event.country,
            company=event.company,
            joined_at=event.joined_at
        )
        
        # Mark event as processed
        with self.db.get_cursor() as cur:
            cur.execute("""
                UPDATE events_raw
                SET processed = TRUE, processed_at = NOW()
                WHERE id = %s
            """, (event_id,))
        
        return {
            "status": "processed",
            "user_id": event.userId,
            "is_senior": is_senior,
            "seniority_level": seniority_level,
            "event_id": event_id
        }


# Singleton instance
_processor: Optional[EventProcessor] = None


def get_event_processor() -> EventProcessor:
    """Get event processor instance (singleton)."""
    global _processor
    if _processor is None:
        _processor = EventProcessor()
    return _processor

