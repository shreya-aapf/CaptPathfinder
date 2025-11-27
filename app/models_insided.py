"""
inSided (Gainsight Community) Webhook Models
=============================================
Based on: https://api2-us-west-2.insided.com/docs/#section/Webhooks/Event-payload-examples

inSided webhook events for user profile updates.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import datetime


class InSidedWebhookEvent(BaseModel):
    """
    inSided webhook event payload.
    
    Event types we care about:
    - integration.UserProfileUpdated
    
    Reference: https://api2-us-west-2.insided.com/docs/#section/Webhooks/Event-payload-examples
    """
    event: str = Field(..., description="Event type (e.g., 'integration.UserProfileUpdated')")
    userId: str = Field(..., description="User ID in inSided")
    username: Optional[str] = Field(None, description="Username")
    profileFieldId: Optional[str] = Field(None, description="Profile field ID")
    profileField: Optional[str] = Field(None, description="Profile field name")
    value: Optional[str] = Field(None, description="New value")
    oldValue: Optional[str] = Field(None, description="Old value")
    
    # Additional inSided fields
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    communityId: Optional[str] = Field(None, description="Community ID")
    
    # Raw payload for any additional fields
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw webhook data")
    
    class Config:
        extra = "allow"  # Allow additional fields from inSided


class InSidedUser(BaseModel):
    """
    User data from inSided API.
    
    Reference: https://api2-us-west-2.insided.com/docs/user/
    """
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: Optional[str] = None
    displayName: Optional[str] = Field(None, alias="display_name")
    
    # Custom fields (profile fields)
    customFields: Optional[Dict[str, Any]] = Field(None, alias="custom_fields")
    
    # Additional user data
    country: Optional[str] = None
    company: Optional[str] = None
    jobTitle: Optional[str] = Field(None, alias="job_title")
    registeredAt: Optional[datetime] = Field(None, alias="registered_at")
    
    class Config:
        populate_by_name = True
        extra = "allow"

