"""add celery task status table

Revision ID: g7h8i9j0k1l2
Revises: f1a2b3c4d5e6
Create Date: 2025-11-14 20:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create celery_task_status table
    op.create_table(
        'celery_task_status',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=255), nullable=False),
        sa.Column('task_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('current_step', sa.String(length=255), nullable=True),
        sa.Column('result_json', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('followed_channel_id', sa.Integer(), nullable=True),
        sa.Column('youtube_video_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_celery_task_status_task_id', 'celery_task_status', ['task_id'], unique=True)
    op.create_index('idx_celery_task_status_status', 'celery_task_status', ['status'], unique=False)
    op.create_index('idx_celery_task_status_followed_channel', 'celery_task_status', ['followed_channel_id'], unique=False)
    op.create_index('idx_celery_task_status_youtube_video', 'celery_task_status', ['youtube_video_id'], unique=False)
    op.create_index('idx_celery_task_status_created_at', 'celery_task_status', ['created_at'], unique=False)
    
    # Add task_id columns to followed_channels table
    op.add_column('followed_channels', sa.Column('last_check_task_id', sa.String(length=255), nullable=True))
    op.add_column('followed_channels', sa.Column('last_backfill_task_id', sa.String(length=255), nullable=True))
    op.create_index('idx_followed_channel_last_check_task', 'followed_channels', ['last_check_task_id'], unique=False)
    op.create_index('idx_followed_channel_last_backfill_task', 'followed_channels', ['last_backfill_task_id'], unique=False)


def downgrade() -> None:
    # Remove indexes from followed_channels
    op.drop_index('idx_followed_channel_last_backfill_task', table_name='followed_channels')
    op.drop_index('idx_followed_channel_last_check_task', table_name='followed_channels')
    
    # Remove columns from followed_channels
    op.drop_column('followed_channels', 'last_backfill_task_id')
    op.drop_column('followed_channels', 'last_check_task_id')
    
    # Drop indexes from celery_task_status
    op.drop_index('idx_celery_task_status_created_at', table_name='celery_task_status')
    op.drop_index('idx_celery_task_status_youtube_video', table_name='celery_task_status')
    op.drop_index('idx_celery_task_status_followed_channel', table_name='celery_task_status')
    op.drop_index('idx_celery_task_status_status', table_name='celery_task_status')
    op.drop_index('idx_celery_task_status_task_id', table_name='celery_task_status')
    
    # Drop table
    op.drop_table('celery_task_status')





