"""ensure_user_settings_defaults_and_fix_enum_values

Revision ID: 7d0e08ad4b92
Revises: 9fb1bc92c905
Create Date: 2025-12-01 23:52:04.778798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7d0e08ad4b92'
down_revision: Union[str, Sequence[str], None] = '9fb1bc92c905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ensure user_settings defaults are correct:
    1. Fix any lowercase enum values to uppercase (daily -> DAILY, weekly -> WEEKLY)
    2. Create user_settings rows for any users that don't have them
    """
    # Fix lowercase enum values to uppercase
    # SQLAlchemy stores enum NAME, not value, so we need DAILY not daily
    op.execute("""
        UPDATE user_settings
        SET subscription_check_frequency = 'DAILY'
        WHERE subscription_check_frequency = 'daily'
    """)

    op.execute("""
        UPDATE user_settings
        SET subscription_check_frequency = 'WEEKLY'
        WHERE subscription_check_frequency = 'weekly'
    """)

    # Create user_settings for any users that don't have them yet
    # This ensures all users have default settings
    # Default to "DAILY" at 00:00
    # Careful with the frequency, it is an enum, so should be "DAILY" or "WEEKLY" not "daily" or "weekly"
    op.execute("""
        INSERT INTO user_settings (user_id, subscription_check_frequency, preferred_check_hour, preferred_check_minute, created_at, updated_at)
        SELECT
            u.id,
            'DAILY',
            0,
            0,  
            datetime('now'),
            datetime('now')
        FROM users u
        LEFT JOIN user_settings us ON u.id = us.user_id
        WHERE us.id IS NULL
    """)


def downgrade() -> None:
    """Downgrade schema - no changes needed as this is a data migration."""
    # We don't need to reverse the enum fix or remove the created settings
    # This would be destructive and unnecessary
    pass
