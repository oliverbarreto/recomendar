"""
User Settings API Request/Response Schemas
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator, field_serializer
from typing import Optional, Any
from datetime import datetime
from enum import Enum


class SubscriptionCheckFrequencyEnum(str, Enum):
    """Subscription check frequency enum for API"""
    DAILY = "daily"
    WEEKLY = "weekly"


class UserSettingsUpdateRequest(BaseModel):
    """Request schema for updating user settings"""
    subscription_check_frequency: Optional[SubscriptionCheckFrequencyEnum] = Field(
        default=None,
        description="Subscription check frequency (daily or weekly)"
    )
    preferred_check_hour: Optional[int] = Field(
        default=None,
        ge=0,
        le=23,
        description="Preferred check hour in UTC (0-23)"
    )
    preferred_check_minute: Optional[int] = Field(
        default=None,
        ge=0,
        le=59,
        description="Preferred check minute (0-59)"
    )
    timezone: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Preferred timezone (IANA timezone string, e.g., 'Europe/Madrid', 'America/New_York')"
    )


class UserSettingsResponse(BaseModel):
    """Response schema for user settings"""
    id: int = Field(..., description="Settings ID")
    user_id: int = Field(..., description="User ID")
    subscription_check_frequency: str = Field(..., description="Check frequency (daily or weekly)")
    preferred_check_hour: int = Field(..., description="Preferred check hour in UTC (0-23)")
    preferred_check_minute: int = Field(..., description="Preferred check minute (0-59)")
    timezone: str = Field(..., description="Preferred timezone (IANA timezone string)")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True
    )

    @field_serializer('subscription_check_frequency')
    def serialize_frequency(self, value: Any) -> str:
        """Serialize enum to string value"""
        if hasattr(value, 'value'):
            return value.value
        return str(value)







