"""add_executed_by_to_notifications

Revision ID: 37bd0516b334
Revises: h9i0j1k2l3m4
Create Date: 2025-12-01 13:05:06.579687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37bd0516b334'
down_revision: Union[str, Sequence[str], None] = 'h9i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add executed_by column to notifications table."""
    # Add executed_by column with default value 'user'
    op.add_column('notifications',
        sa.Column('executed_by', sa.String(20), server_default='user', nullable=False)
    )
    # Create index for filtering by executed_by
    op.create_index('ix_notifications_executed_by', 'notifications', ['executed_by'])


def downgrade() -> None:
    """Remove executed_by column from notifications table."""
    # Drop index first
    op.drop_index('ix_notifications_executed_by', 'notifications')
    # Drop column
    op.drop_column('notifications', 'executed_by')
