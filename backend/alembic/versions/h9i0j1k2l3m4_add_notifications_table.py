"""add notifications table

Revision ID: h9i0j1k2l3m4
Revises: g7h8i9j0k1l2
Create Date: 2025-11-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'h9i0j1k2l3m4'
down_revision: Union[str, None] = 'g7h8i9j0k1l2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('data_json', sa.JSON(), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes for efficient queries
    op.create_index('idx_notification_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('idx_notification_type', 'notifications', ['type'], unique=False)
    op.create_index('idx_notification_read', 'notifications', ['read'], unique=False)
    op.create_index('idx_notification_created_at', 'notifications', ['created_at'], unique=False)
    
    # Composite indexes for common query patterns
    op.create_index('idx_notification_user_read_created', 'notifications', ['user_id', 'read', 'created_at'], unique=False)
    op.create_index('idx_notification_user_created', 'notifications', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop composite indexes
    op.drop_index('idx_notification_user_created', table_name='notifications')
    op.drop_index('idx_notification_user_read_created', table_name='notifications')
    
    # Drop single column indexes
    op.drop_index('idx_notification_created_at', table_name='notifications')
    op.drop_index('idx_notification_read', table_name='notifications')
    op.drop_index('idx_notification_type', table_name='notifications')
    op.drop_index('idx_notification_user_id', table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')



