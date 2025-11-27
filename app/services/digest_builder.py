"""
Digest Builder Service
======================
Handles sending of pending digests to stakeholders via Automation Anywhere.
"""

import logging
from typing import List, Optional
from datetime import datetime

from ..database import get_db
from ..models import DigestPayload, DigestEntry
from .aa_integration import get_aa_client

logger = logging.getLogger(__name__)


class DigestSender:
    """Sends pending digests via Automation Anywhere."""
    
    def __init__(self):
        """Initialize digest sender."""
        self.db = get_db()
        self.aa_client = get_aa_client()
    
    def get_pending_digests(self) -> List[dict]:
        """
        Get pending digests that need to be sent.
        
        Uses SELECT FOR UPDATE SKIP LOCKED for concurrent processing safety.
        """
        with self.db.get_cursor() as cur:
            cur.execute("""
                SELECT 
                    id, week_start, week_end, channel, payload, created_at
                FROM digests
                WHERE NOT sent
                ORDER BY created_at ASC
                LIMIT 10
                FOR UPDATE SKIP LOCKED
            """)
            
            digests = cur.fetchall()
            logger.info(f"Found {len(digests)} pending digests")
            return digests
    
    def mark_digest_sent(self, digest_id: int):
        """Mark a digest as sent."""
        with self.db.get_cursor() as cur:
            cur.execute("""
                UPDATE digests
                SET sent = TRUE, sent_at = NOW()
                WHERE id = %s
            """, (digest_id,))
            logger.info(f"Marked digest {digest_id} as sent")
    
    def _build_digest_payload(self, digest_row: dict) -> DigestPayload:
        """Build DigestPayload from database row."""
        payload_json = digest_row['payload']
        users_data = payload_json.get('users', [])
        
        users = [
            DigestEntry(
                user_id=u['user_id'],
                username=u['username'],
                title=u['title'],
                seniority_level=u['seniority_level'],
                country=u.get('country'),
                company=u.get('company'),
                joined_at=datetime.fromisoformat(u['joined_at']) if u.get('joined_at') else None,
                detected_at=datetime.fromisoformat(u['detected_at'])
            )
            for u in users_data
        ]
        
        return DigestPayload(
            week_start=str(digest_row['week_start']),
            week_end=str(digest_row['week_end']),
            channel=digest_row['channel'],
            users=users,
            total_count=len(users)
        )
    
    async def send_pending_digests(self) -> dict:
        """
        Send all pending digests.
        
        Returns summary of results.
        """
        digests = self.get_pending_digests()
        
        results = {
            "total": len(digests),
            "sent": 0,
            "failed": 0,
            "errors": []
        }
        
        for digest_row in digests:
            digest_id = digest_row['id']
            try:
                # Build payload
                payload = self._build_digest_payload(digest_row)
                
                # Send via AA
                success = await self.aa_client.send_digest(payload)
                
                if success:
                    # Mark as sent
                    self.mark_digest_sent(digest_id)
                    results["sent"] += 1
                    logger.info(
                        f"Successfully sent digest {digest_id} via {payload.channel}"
                    )
                else:
                    results["failed"] += 1
                    results["errors"].append(
                        f"Digest {digest_id}: Send failed (see logs)"
                    )
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"Digest {digest_id}: {str(e)}")
                logger.error(f"Error processing digest {digest_id}: {e}", exc_info=True)
        
        logger.info(f"Digest sending complete: {results}")
        return results


# Singleton instance
_digest_sender: Optional[DigestSender] = None


def get_digest_sender() -> DigestSender:
    """Get digest sender instance (singleton)."""
    global _digest_sender
    if _digest_sender is None:
        _digest_sender = DigestSender()
    return _digest_sender

