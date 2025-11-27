"""
Automation Anywhere Integration
================================
Integrates with Automation Anywhere Control Room using Bot Deploy API v4.
Deploys bots with input variables for email and Teams notifications.

API Documentation: https://docs.automationanywhere.com/bundle/enterprise-v2019/page/deploy-api-supported-v4.html
"""

import httpx
import logging
from typing import Optional, Dict, Any, List
from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import get_settings
from ..models import DigestPayload

logger = logging.getLogger(__name__)


class AutomationAnywhereClient:
    """
    Client for deploying Automation Anywhere bots via Control Room API v4.
    
    Uses Authentication API v2 to get token, then deploys bots with input variables.
    
    Auth API: https://docs.automationanywhere.com/bundle/enterprise-v2019/page/auth-api-supported-v2.html
    Deploy API: https://docs.automationanywhere.com/bundle/enterprise-v2019/page/deploy-api-supported-v4.html
    """
    
    def __init__(self):
        """Initialize AA client with Control Room configuration."""
        self.settings = get_settings()
        self.control_room_url = self.settings.aa_control_room_url.rstrip('/')
        self.username = self.settings.aa_username
        self.api_key = self.settings.aa_api_key
        self.email_bot_id = self.settings.aa_email_bot_id
        self.teams_bot_id = self.settings.aa_teams_bot_id
        self.auth_endpoint = self.settings.aa_auth_endpoint
        
        # API endpoints
        self.deploy_endpoint = f"{self.control_room_url}/v3/automations/deploy"
        
        # Token will be set after authentication
        self.auth_token = None
        self.headers = {
            "Content-Type": "application/json"
        }
    
    async def _authenticate(self) -> str:
        """
        Authenticate with AA Control Room to get access token.
        
        Uses Authentication API v2: 
        https://docs.automationanywhere.com/bundle/enterprise-v2019/page/auth-api-supported-v2.html
        
        Returns:
            Authentication token for use in X-Authorization header
        """
        auth_payload = {
            "username": self.username,
            "apiKey": self.api_key,
            "multipleLogin": False  # Set to True if you need multiple concurrent sessions
        }
        
        logger.info(f"Authenticating user {self.username} with AA Control Room")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.auth_endpoint,
                json=auth_payload,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract token from response
            token = result.get("token")
            if not token:
                raise ValueError("Authentication response did not contain token")
            
            logger.info("Successfully authenticated with AA Control Room")
            return token
    
    async def _ensure_authenticated(self):
        """Ensure we have a valid authentication token."""
        if not self.auth_token:
            self.auth_token = await self._authenticate()
            self.headers["X-Authorization"] = self.auth_token
    
    def _prepare_email_bot_inputs(self, digest: DigestPayload) -> Dict[str, Any]:
        """
        Prepare input variables for email bot.
        
        These variables will be passed to your AA bot as input values.
        Customize based on your bot's input variable names.
        """
        # Build email body HTML
        html_body = self._build_email_html(digest)
        
        # Prepare bot input variables
        # IMPORTANT: Variable names must match your bot's input variable names
        bot_inputs = {
            "emailTo": "stakeholder1@company.com;stakeholder2@company.com",  # Semicolon-separated
            "emailSubject": f"Weekly Senior Executive Digest: {digest.week_start} - {digest.week_end}",
            "emailBody": html_body,
            "isHTML": "true",  # String value for boolean
            "weekStart": digest.week_start,
            "weekEnd": digest.week_end,
            "totalCount": str(digest.total_count)  # Convert to string
        }
        
        return bot_inputs
    
    def _build_email_html(self, digest: DigestPayload) -> str:
        """Build HTML email body."""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th {{ background-color: #007bff; color: white; padding: 12px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                tr:hover {{ background-color: #f8f9fa; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Weekly Senior Executive Detections</h2>
            </div>
            <p><strong>Period:</strong> {digest.week_start} to {digest.week_end}</p>
            <p><strong>Total detections:</strong> {digest.total_count}</p>
            
            <table>
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
            html += f"""
                    <tr>
                        <td>{user.username}</td>
                        <td>{user.title}</td>
                        <td>{user.seniority_level.upper()}</td>
                        <td>{user.country or 'N/A'}</td>
                        <td>{user.company or 'N/A'}</td>
                        <td>{user.detected_at.strftime('%Y-%m-%d')}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html
    
    def _prepare_teams_bot_inputs(self, digest: DigestPayload) -> Dict[str, Any]:
        """
        Prepare input variables for Teams bot.
        
        These variables will be passed to your AA bot as input values.
        Customize based on your bot's input variable names.
        """
        # Build Teams message text (markdown format)
        message_text = f"""**Weekly Senior Executive Detections**

**Period:** {digest.week_start} to {digest.week_end}  
**Total detections:** {digest.total_count}

"""
        
        for user in digest.users:
            message_text += f"""
- **{user.username}** - {user.title} ({user.seniority_level.upper()})  
  {user.company or 'Company N/A'} | {user.country or 'Country N/A'}  
  Detected: {user.detected_at.strftime('%Y-%m-%d')}

"""
        
        # Prepare bot input variables
        # IMPORTANT: Variable names must match your bot's input variable names
        bot_inputs = {
            "teamsChannelWebhook": "https://outlook.office.com/webhook/your-webhook-url",  # Configure this
            "messageText": message_text,
            "messageType": "markdown",
            "weekStart": digest.week_start,
            "weekEnd": digest.week_end,
            "totalCount": str(digest.total_count)
        }
        
        return bot_inputs
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _deploy_bot(
        self,
        bot_id: str,
        bot_inputs: Dict[str, Any],
        bot_name: str = "Bot"
    ) -> Dict[str, Any]:
        """
        Deploy an Automation Anywhere bot using the Bot Deploy API v3.
        
        API Reference: https://docs.automationanywhere.com/bundle/enterprise-v2019/page/deploy-api-supported-v4.html
        
        Args:
            bot_id: The file ID/bot ID of the bot in Control Room
            bot_inputs: Dictionary of input variable names and values
            bot_name: Name for logging purposes
            
        Returns:
            API response with deployment ID and status
        """
        # Ensure we're authenticated
        await self._ensure_authenticated()
        
        # Convert bot inputs to AA API format
        # Input variables as nested dictionary structure
        formatted_inputs = {}
        for key, value in bot_inputs.items():
            formatted_inputs[key] = {
                "type": "STRING",
                "string": value
            }
        
        # Build deployment request payload based on AA API v3 structure
        payload = {
            "botId": int(bot_id) if bot_id.isdigit() else bot_id,  # Can be int or string fileId
            "automationName": bot_name,
            "description": f"Deployed by CaptPathfinder - {bot_name}",
            "botInput": formatted_inputs,
            "automationPriority": "PRIORITY_MEDIUM",
            "runElevated": False,
            "hideBotAgentUi": False
        }
        
        logger.info(f"Deploying {bot_name} (Bot ID: {bot_id})")
        logger.debug(f"Deployment payload: {payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.deploy_endpoint,
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            deployment_id = result.get('deploymentId') or result.get('automationId')
            logger.info(f"{bot_name} deployed successfully. Deployment ID: {deployment_id}")
            return result
    
    async def send_email_digest(self, digest: DigestPayload) -> bool:
        """
        Send digest via email by deploying the email bot.
        
        Returns True if successful, False otherwise.
        """
        try:
            logger.info(
                f"Sending email digest for week {digest.week_start} - {digest.week_end}"
            )
            
            # Prepare bot input variables
            bot_inputs = self._prepare_email_bot_inputs(digest)
            
            # Deploy the email bot
            result = await self._deploy_bot(
                bot_id=self.email_bot_id,
                bot_inputs=bot_inputs,
                bot_name="Email Bot"
            )
            
            logger.info(f"Email digest sent successfully: {result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email digest: {e}", exc_info=True)
            return False
    
    async def send_teams_digest(self, digest: DigestPayload) -> bool:
        """
        Send digest to Teams by deploying the Teams bot.
        
        Returns True if successful, False otherwise.
        """
        try:
            logger.info(
                f"Sending Teams digest for week {digest.week_start} - {digest.week_end}"
            )
            
            # Prepare bot input variables
            bot_inputs = self._prepare_teams_bot_inputs(digest)
            
            # Deploy the Teams bot
            result = await self._deploy_bot(
                bot_id=self.teams_bot_id,
                bot_inputs=bot_inputs,
                bot_name="Teams Bot"
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

