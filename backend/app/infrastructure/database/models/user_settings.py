"""
UserSettings SQLAlchemy model

Stores user preferences for the follow channel feature.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.infrastructure.database.connection import Base


class SubscriptionCheckFrequency(enum.Enum):
    """Frequency for checking followed channels for new videos"""
    DAILY = "daily"
    WEEKLY = "weekly"


class UserSettingsModel(Base):
    """
    SQLAlchemy model for UserSettings entity

    Stores user preferences for the follow channel feature.
    One-to-one relationship with User.
    """
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)

    # Subscription check frequency preference
    subscription_check_frequency = Column(
        Enum(SubscriptionCheckFrequency),
        nullable=False,
        default=SubscriptionCheckFrequency.DAILY
    )

    # Preferred check time (in UTC)
    preferred_check_hour = Column(Integer, nullable=False, server_default='2')  # 0-23
    preferred_check_minute = Column(Integer, nullable=False, server_default='0')  # 0-59

    # Preferred timezone for scheduled checks
    timezone = Column(String(100), nullable=False, server_default='Europe/Madrid')

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="user_settings")

    # Constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_settings_user_id'),
    )

    def __repr__(self):
        return f"<UserSettingsModel(id={self.id}, user_id={self.user_id}, frequency='{self.subscription_check_frequency.value}')>"







