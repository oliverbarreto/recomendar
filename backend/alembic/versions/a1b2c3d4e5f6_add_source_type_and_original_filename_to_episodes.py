"""Add source_type and original_filename to episodes

Revision ID: a1b2c3d4e5f6
Revises: d6d8d07b41e3
Create Date: 2025-10-18 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'd6d8d07b41e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add source_type column with default value "youtube"
    op.add_column('episodes', sa.Column('source_type', sa.String(length=20), nullable=True, default='youtube'))
    
    # Update existing episodes to have source_type = "youtube"
    op.execute("UPDATE episodes SET source_type = 'youtube' WHERE source_type IS NULL")
    
    # Add original_filename column (nullable)
    op.add_column('episodes', sa.Column('original_filename', sa.String(length=500), nullable=True))
    
    # Create index on source_type for performance
    op.create_index('idx_episode_source_type', 'episodes', ['source_type'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the index
    op.drop_index('idx_episode_source_type', table_name='episodes')
    
    # Drop the columns
    op.drop_column('episodes', 'original_filename')
    op.drop_column('episodes', 'source_type')


