"""add_check_time_to_user_settings_and_remove_twice_weekly

Revision ID: 9fb1bc92c905
Revises: 37bd0516b334
Create Date: 2025-12-01 13:12:27.458675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fb1bc92c905'
down_revision: Union[str, Sequence[str], None] = '37bd0516b334'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add preferred check time fields to user_settings and migrate TWICE_WEEKLY to DAILY."""
    # Add preferred check time fields
    op.add_column('user_settings',
        sa.Column('preferred_check_hour', sa.Integer(), server_default='2', nullable=False)
    )
    op.add_column('user_settings',
        sa.Column('preferred_check_minute', sa.Integer(), server_default='0', nullable=False)
    )

    # Migrate existing TWICE_WEEKLY frequency to DAILY
    # Note: In SQLite, we can't easily modify enum constraints, but we can update the data
    op.execute("UPDATE user_settings SET subscription_check_frequency = 'DAILY' WHERE subscription_check_frequency = 'TWICE_WEEKLY'")

    # Note: The enum constraint will be updated in the model definition
    # SQLite doesn't enforce enum constraints at the database level like PostgreSQL does


def downgrade() -> None:
    """Remove preferred check time fields from user_settings."""
    # Note: We cannot restore TWICE_WEEKLY values after migration
    # Drop the new columns
    op.drop_column('user_settings', 'preferred_check_minute')
    op.drop_column('user_settings', 'preferred_check_hour')
