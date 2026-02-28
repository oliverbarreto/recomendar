"""
UserSettings domain entity

Stores user preferences for the follow channel feature.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from app.domain.entities.followed_channel import SubscriptionCheckFrequency


@dataclass
class UserSettings:
    """
    UserSettings domain entity representing user preferences

    Stores user preferences for the follow channel feature.
    One-to-one relationship with User.
    """
    id: Optional[int]
    user_id: int
    subscription_check_frequency: SubscriptionCheckFrequency = SubscriptionCheckFrequency.DAILY
    preferred_check_hour: int = 2  # Default: 2 AM UTC
    preferred_check_minute: int = 0  # Default: 0 minutes
    timezone: str = "Europe/Madrid"  # Default timezone
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate and initialize user settings"""
        # Validate required fields
        if self.user_id <= 0:
            raise ValueError("Valid user_id is required")

        # Validate preferred check time
        if not (0 <= self.preferred_check_hour <= 23):
            raise ValueError("preferred_check_hour must be between 0 and 23")
        if not (0 <= self.preferred_check_minute <= 59):
            raise ValueError("preferred_check_minute must be between 0 and 59")

        # Validate timezone using zoneinfo
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(self.timezone)
        except Exception:
            raise ValueError(f"Invalid timezone: {self.timezone}")

        # Set timestamps
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def update_subscription_frequency(self, frequency: SubscriptionCheckFrequency) -> None:
        """
        Update subscription check frequency

        Args:
            frequency: New check frequency (daily or weekly)
        """
        self.subscription_check_frequency = frequency
        self.updated_at = datetime.utcnow()

    def update_check_time(self, hour: int, minute: int) -> None:
        """
        Update preferred check time

        Args:
            hour: Hour in 24-hour format (0-23)
            minute: Minute (0-59)
        """
        if not (0 <= hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
        if not (0 <= minute <= 59):
            raise ValueError("Minute must be between 0 and 59")

        self.preferred_check_hour = hour
        self.preferred_check_minute = minute
        self.updated_at = datetime.utcnow()

    def update_timezone(self, timezone: str) -> None:
        """
        Update preferred timezone

        Args:
            timezone: IANA timezone string (e.g., 'Europe/Madrid', 'America/New_York')
        """
        from zoneinfo import ZoneInfo
        try:
            ZoneInfo(timezone)  # Validate
        except Exception:
            raise ValueError(f"Invalid timezone: {timezone}")

        self.timezone = timezone
        self.updated_at = datetime.utcnow()







