"""Add media_file_size to episodes and update channel constraints

Revision ID: 138dbddf3ea3
Revises: 79b4815371be
Create Date: 2025-09-16 07:01:44.464565

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '138dbddf3ea3'
down_revision: Union[str, Sequence[str], None] = '79b4815371be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # For SQLite, we need to recreate the table to change NULL constraints
    # First, update any existing NULL website_url values with a placeholder
    op.execute("UPDATE channels SET website_url = 'https://example.com' WHERE website_url IS NULL OR website_url = ''")

    # Add media_file_size to episodes with default value 0
    op.add_column('episodes', sa.Column('media_file_size', sa.Integer(), nullable=True, default=0))

    # Update existing episodes to have media_file_size = 0
    op.execute("UPDATE episodes SET media_file_size = 0 WHERE media_file_size IS NULL")

    # Note: SQLite doesn't support ALTER COLUMN to change NULL constraints
    # The website_url NOT NULL constraint will be enforced at the application level
    # and in future table recreations


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the media_file_size column
    op.drop_column('episodes', 'media_file_size')
    # Note: Cannot revert website_url constraint change in SQLite
