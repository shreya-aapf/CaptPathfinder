"""
inSided API Client
==================
Client for fetching user data from inSided (Gainsight Community) API.

API Documentation: https://api2-us-west-2.insided.com/docs/
"""

import httpx
import logging
from typing import Optional
from datetime import datetime

from ..config import get_settings
from .models_insided import InSidedUser

logger = logging.getLogger(__name__)


class InSidedAPIClient:
    """Client for inSided API to fetch user profile data."""
    
    def __init__(self):
        """Initialize inSided API client."""
        self.settings = get_settings()
        
        # inSided API configuration (from .env)
        self.api_base_url = self.settings.community_api_url or "https://api2-us-west-2.insided.com"
        self.api_key = self.settings.community_api_key
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_user(self, user_id: str) -> Optional[InSidedUser]:
        """
        Fetch user profile from inSided API.
        
        API: GET /users/{userId}
        Reference: https://api2-us-west-2.insided.com/docs/user/
        
        Args:
            user_id: The inSided user ID
            
        Returns:
            InSidedUser object with profile data, or None if failed
        """
        try:
            url = f"{self.api_base_url}/users/{user_id}"
            
            logger.info(f"Fetching user profile from inSided: {user_id}")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse response into InSidedUser model
                user = InSidedUser(**data)
                
                logger.info(f"Successfully fetched user {user_id} from inSided")
                return user
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching user {user_id} from inSided: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching user {user_id} from inSided: {e}", exc_info=True)
            return None
    
    async def get_user_custom_field(self, user_id: str, field_name: str) -> Optional[str]:
        """
        Get a specific custom field value for a user.
        
        Args:
            user_id: The inSided user ID
            field_name: The custom field name (e.g., "Job Title")
            
        Returns:
            Field value as string, or None if not found
        """
        user = await self.get_user(user_id)
        
        if not user:
            return None
        
        # Check if field is in customFields
        if user.customFields and field_name in user.customFields:
            return str(user.customFields[field_name])
        
        # Check direct field mapping
        field_mapping = {
            "Job Title": user.jobTitle,
            "Country": user.country,
            "Company": user.company,
        }
        
        return field_mapping.get(field_name)


# Singleton instance
_insided_client: Optional[InSidedAPIClient] = None


def get_insided_client() -> InSidedAPIClient:
    """Get inSided API client instance (singleton)."""
    global _insided_client
    if _insided_client is None:
        _insided_client = InSidedAPIClient()
    return _insided_client

