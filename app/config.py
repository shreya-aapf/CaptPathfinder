"""
Configuration module for CaptPathfinder.
Loads environment variables and provides typed configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    supabase_db_url: str
    
    # Automation Anywhere Integration
    aa_control_room_url: str
    aa_api_key: str
    aa_email_bot_id: str
    aa_teams_bot_id: str
    aa_run_as_user_id: str
    
    # Optional: Username/Password auth (API key recommended)
    aa_username: Optional[str] = None
    aa_password: Optional[str] = None
    
    # Community Platform API
    community_api_url: Optional[str] = None
    community_api_key: Optional[str] = None
    
    # Application Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Supabase Storage (for reports)
    supabase_storage_url: Optional[str] = None
    supabase_storage_bucket: str = "reports"
    supabase_anon_key: Optional[str] = None
    
    # Processing
    batch_size: int = 100
    max_retries: int = 3
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings (singleton)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings

