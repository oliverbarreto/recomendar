"""add youtube_channel_description to followed_channels

Revision ID: 36ae9abb89c6
Revises: 7f7abf5fdf3f
Create Date: 2025-12-02 18:38:56.748200

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '36ae9abb89c6'
down_revision: Union[str, Sequence[str], None] = '7f7abf5fdf3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add youtube_channel_description column to followed_channels table
    op.add_column('followed_channels', sa.Column('youtube_channel_description', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove youtube_channel_description column from followed_channels table
    op.drop_column('followed_channels', 'youtube_channel_description')
