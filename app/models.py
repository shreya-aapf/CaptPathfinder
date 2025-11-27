"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WebhookEvent(BaseModel):
    """Webhook event from community platform."""
    userId: str = Field(..., description="User ID from community platform")
    username: str = Field(..., description="User's display name")
    profileFieldId: Optional[str] = Field(None, description="Field ID")
    profileField: str = Field(..., description="Name of the profile field")
    value: str = Field(..., description="New value")
    oldValue: Optional[str] = Field(None, description="Previous value")
    
    # Optional fields that might come from webhook or need to be fetched
    country: Optional[str] = None
    company: Optional[str] = None
    joined_at: Optional[datetime] = None


class UserMetadata(BaseModel):
    """Additional user metadata from community API."""
    user_id: str
    country: Optional[str] = None
    company: Optional[str] = None
    joined_at: Optional[datetime] = None


class ClassificationResult(BaseModel):
    """Result of title classification."""
    is_senior: bool
    seniority_level: str  # 'csuite', 'vp', or ''
    title: str
    normalized_title: str


class DigestEntry(BaseModel):
    """Entry in a weekly digest."""
    user_id: str
    username: str
    title: str
    seniority_level: str
    country: Optional[str]
    company: Optional[str]
    joined_at: Optional[datetime]
    detected_at: datetime


class DigestPayload(BaseModel):
    """Payload for sending digest to Automation Anywhere."""
    week_start: str
    week_end: str
    channel: str
    users: list[DigestEntry]
    total_count: int


class MonthEndReportSummary(BaseModel):
    """Summary for month-end report."""
    month: str
    total_detections: int
    csuite_count: int
    vp_count: int
    top_countries: dict[str, int]

