"""
Automation Anywhere Integration
================================
Provides integration with AA bots for sending emails and Teams messages.
"""

import httpx
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models import DigestPayload

logger = logging.getLogger(__name__)


class AutomationAnywhereClient:
    """Client for interacting with Automation Anywhere bots."""
    
    def __init__(self):
        """Initialize AA client."""
        self.settings = get_settings()
        self.email_bot_url = self.settings.aa_email_bot_url
        self.email_bot_api_key = self.settings.aa_email_bot_api_key
        self.teams_bot_url = self.settings.aa_teams_bot_url
        self.teams_bot_api_key = self.settings.aa_teams_bot_api_key
    
    def _format_digest_for_email(self, digest: DigestPayload) -> Dict[str, Any]:
        """
        Format digest payload for email bot.
        
        Customize this based on your AA email bot's expected input format.
        """
        # Build HTML email body
        html_body = f"""
        <html>
        <body>
            <h2>Weekly Senior Executive Detections</h2>
            <p>Period: {digest.week_start} to {digest.week_end}</p>
            <p>Total detections: {digest.total_count}</p>
            
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Title</th>
                        <th>Level</th>
                        <th>Country</th>
                        <th>Company</th>
                        <th>Detected</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for user in digest.users:
            html_body += f"""
                    <tr>
                        <td>{user.username}</td>
                        <td>{user.title}</td>
                        <td>{user.seniority_level.upper()}</td>
                        <td>{user.country or 'N/A'}</td>
                        <td>{user.company or 'N/A'}</td>
                        <td>{user.detected_at.strftime('%Y-%m-%d')}</td>
                    </tr>
            """
        
        html_body += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Format for AA email bot
        return {
            "to": ["stakeholder1@company.com", "stakeholder2@company.com"],
            "subject": f"Weekly Senior Executive Digest: {digest.week_start} - {digest.week_end}",
            "body": html_body,
            "is_html": True
        }
    
    def _format_digest_for_teams(self, digest: DigestPayload) -> Dict[str, Any]:
        """
        Format digest payload for Teams bot.
        
        Customize this based on your AA Teams bot's expected input format.
        """
        # Build adaptive card or simple message
        message_text = f"""
**Weekly Senior Executive Detections**

**Period:** {digest.week_start} to {digest.week_end}  
**Total detections:** {digest.total_count}

"""
        
        for user in digest.users:
            message_text += f"""
- **{user.username}** - {user.title} ({user.seniority_level.upper()})  
  {user.company or 'Company N/A'} | {user.country or 'Country N/A'}  
  Detected: {user.detected_at.strftime('%Y-%m-%d')}

"""
        
        # Format for AA Teams bot
        return {
            "channel_url": "https://teams.microsoft.com/l/channel/...",  # Configure this
            "message": message_text,
            "message_type": "markdown"
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _send_request(
        self,
        url: str,
        api_key: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Send HTTP request to AA bot with retry logic.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    
    async def send_email_digest(self, digest: DigestPayload) -> bool:
        """
        Send digest via email through AA bot.
        
        Returns True if successful, False otherwise.
        """
        try:
            logger.info(
                f"Sending email digest for week {digest.week_start} - {digest.week_end}"
            )
            
            payload = self._format_digest_for_email(digest)
            result = await self._send_request(
                self.email_bot_url,
                self.email_bot_api_key,
                payload
            )
            
            logger.info(f"Email digest sent successfully: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email digest: {e}", exc_info=True)
            return False
    
    async def send_teams_digest(self, digest: DigestPayload) -> bool:
        """
        Send digest to Teams through AA bot.
        
        Returns True if successful, False otherwise.
        """
        try:
            logger.info(
                f"Sending Teams digest for week {digest.week_start} - {digest.week_end}"
            )
            
            payload = self._format_digest_for_teams(digest)
            result = await self._send_request(
                self.teams_bot_url,
                self.teams_bot_api_key,
                payload
            )
            
            logger.info(f"Teams digest sent successfully: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Teams digest: {e}", exc_info=True)
            return False
    
    async def send_digest(self, digest: DigestPayload) -> bool:
        """
        Send digest to appropriate channel.
        
        Routes to email or Teams based on digest.channel.
        """
        if digest.channel == "email":
            return await self.send_email_digest(digest)
        elif digest.channel == "teams":
            return await self.send_teams_digest(digest)
        else:
            logger.error(f"Unknown channel: {digest.channel}")
            return False


# Singleton instance
_aa_client: Optional[AutomationAnywhereClient] = None


def get_aa_client() -> AutomationAnywhereClient:
    """Get AA client instance (singleton)."""
    global _aa_client
    if _aa_client is None:
        _aa_client = AutomationAnywhereClient()
    return _aa_client

