"""add_video_id_index_and_unique_constraint

Revision ID: d6d8d07b41e3
Revises: 138dbddf3ea3
Create Date: 2025-10-05 20:01:48.909785

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6d8d07b41e3'
down_revision: Union[str, Sequence[str], None] = '138dbddf3ea3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add unique constraint on channel_id + video_id combination
    # This ensures video_id is unique per channel, preventing duplicate episodes
    # Note: idx_episode_channel_video already exists from initial migration (unique=True)
    # This migration is primarily for documentation and future-proofing

    # Add standalone index on video_id for fast lookups by video_id alone
    op.create_index(
        'idx_episode_video_id_lookup',
        'episodes',
        ['video_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the video_id lookup index
    op.drop_index('idx_episode_video_id_lookup', table_name='episodes')
