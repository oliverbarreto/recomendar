"""add_follow_channel_feature

Add tables for follow channel feature:
- followed_channels: Stores YouTube channels users follow
- youtube_videos: Stores discovered videos from followed channels
- user_settings: Stores user preferences for subscription checks

Revision ID: f1a2b3c4d5e6
Revises: 210e7d798b58
Create Date: 2025-01-03 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, Sequence[str], None] = '210e7d798b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create tables for follow channel feature"""
    
    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subscription_check_frequency', sa.String(length=20), nullable=False, server_default='daily'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_settings_user_id')
    )
    op.create_index(op.f('ix_user_settings_user_id'), 'user_settings', ['user_id'], unique=True)
    
    # Create followed_channels table
    op.create_table(
        'followed_channels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('youtube_channel_id', sa.String(length=255), nullable=False),
        sa.Column('youtube_channel_name', sa.String(length=255), nullable=False),
        sa.Column('youtube_channel_url', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('auto_approve', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('auto_approve_channel_id', sa.Integer(), nullable=True),
        sa.Column('last_checked', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['auto_approve_channel_id'], ['channels.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('youtube_channel_id', 'user_id', name='uq_followed_channel_user')
    )
    op.create_index(op.f('ix_followed_channels_user_id'), 'followed_channels', ['user_id'], unique=False)
    op.create_index(op.f('ix_followed_channels_youtube_channel_id'), 'followed_channels', ['youtube_channel_id'], unique=False)
    op.create_index('idx_followed_channel_last_checked', 'followed_channels', ['last_checked'], unique=False)
    
    # Create youtube_videos table
    op.create_table(
        'youtube_videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.String(length=255), nullable=False),
        sa.Column('followed_channel_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('like_count', sa.Integer(), nullable=True),
        sa.Column('comment_count', sa.Integer(), nullable=True),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('state', sa.String(length=20), nullable=False, server_default='pending_review'),
        sa.Column('episode_id', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['followed_channel_id'], ['followed_channels.id'], ),
        sa.ForeignKeyConstraint(['episode_id'], ['episodes.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('video_id', name='uq_youtube_video_id')
    )
    op.create_index(op.f('ix_youtube_videos_video_id'), 'youtube_videos', ['video_id'], unique=True)
    op.create_index(op.f('ix_youtube_videos_followed_channel_id'), 'youtube_videos', ['followed_channel_id'], unique=False)
    op.create_index('idx_youtube_video_state', 'youtube_videos', ['state'], unique=False)
    op.create_index('idx_youtube_video_publish_date', 'youtube_videos', ['publish_date'], unique=False)
    op.create_index('idx_youtube_video_channel_state', 'youtube_videos', ['followed_channel_id', 'state'], unique=False)
    op.create_index('idx_youtube_video_episode_id', 'youtube_videos', ['episode_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema: Drop tables for follow channel feature"""
    
    # Drop youtube_videos table
    op.drop_index('idx_youtube_video_episode_id', table_name='youtube_videos')
    op.drop_index('idx_youtube_video_channel_state', table_name='youtube_videos')
    op.drop_index('idx_youtube_video_publish_date', table_name='youtube_videos')
    op.drop_index('idx_youtube_video_state', table_name='youtube_videos')
    op.drop_index(op.f('ix_youtube_videos_followed_channel_id'), table_name='youtube_videos')
    op.drop_index(op.f('ix_youtube_videos_video_id'), table_name='youtube_videos')
    op.drop_table('youtube_videos')
    
    # Drop followed_channels table
    op.drop_index('idx_followed_channel_last_checked', table_name='followed_channels')
    op.drop_index(op.f('ix_followed_channels_youtube_channel_id'), table_name='followed_channels')
    op.drop_index(op.f('ix_followed_channels_user_id'), table_name='followed_channels')
    op.drop_table('followed_channels')
    
    # Drop user_settings table
    op.drop_index(op.f('ix_user_settings_user_id'), table_name='user_settings')
    op.drop_table('user_settings')







