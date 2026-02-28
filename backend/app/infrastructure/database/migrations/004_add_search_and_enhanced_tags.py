"""Add FTS5 search support and enhanced tag functionality

Revision ID: 004
Revises: 003
Create Date: 2025-09-09 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Add FTS5 search support and enhanced tag functionality"""
    
    # Enable FTS5 extension (SQLite should have it by default in recent versions)
    connection = op.get_bind()
    
    # Add new columns to tags table for enhanced functionality
    with op.batch_alter_table('tags', schema=None) as batch_op:
        batch_op.add_column(sa.Column('color', sa.String(7), nullable=False, server_default='#3B82F6'))
        batch_op.add_column(sa.Column('usage_count', sa.Integer, nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('last_used_at', sa.DateTime, nullable=True))
        batch_op.add_column(sa.Column('is_system_tag', sa.Boolean, nullable=False, server_default='false'))
    
    # Create indexes for improved performance
    op.create_index('idx_tags_channel_name', 'tags', ['channel_id', 'name'])
    op.create_index('idx_tags_usage_count', 'tags', ['usage_count'])
    op.create_index('idx_tags_color', 'tags', ['color'])
    
    # Create search performance indexes
    op.create_index('idx_episodes_search_composite', 'episodes', ['channel_id', 'status', 'publication_date'])
    op.create_index('idx_episodes_duration', 'episodes', ['duration'])
    op.create_index('idx_episode_tags_composite', 'episode_tags', ['episode_id', 'tag_id'])
    
    # Create FTS5 virtual table for episode search
    connection.execute(text("""
        CREATE VIRTUAL TABLE episode_search USING fts5(
            episode_id,
            title,
            description,
            keywords,
            content='episodes',
            content_rowid='id'
        );
    """))
    
    # Populate initial FTS5 data from existing episodes
    connection.execute(text("""
        INSERT INTO episode_search(episode_id, title, description, keywords)
        SELECT id, title, description, COALESCE(keywords, '') 
        FROM episodes;
    """))
    
    # Create triggers to keep search index synchronized
    connection.execute(text("""
        CREATE TRIGGER episode_search_insert AFTER INSERT ON episodes 
        BEGIN
            INSERT INTO episode_search(episode_id, title, description, keywords) 
            VALUES (new.id, new.title, new.description, COALESCE(new.keywords, ''));
        END;
    """))
    
    connection.execute(text("""
        CREATE TRIGGER episode_search_update AFTER UPDATE ON episodes 
        BEGIN
            UPDATE episode_search 
            SET title = new.title, 
                description = new.description, 
                keywords = COALESCE(new.keywords, '')
            WHERE episode_id = new.id;
        END;
    """))
    
    connection.execute(text("""
        CREATE TRIGGER episode_search_delete AFTER DELETE ON episodes 
        BEGIN
            DELETE FROM episode_search WHERE episode_id = old.id;
        END;
    """))
    
    # Create trigger to update tag usage count
    connection.execute(text("""
        CREATE TRIGGER update_tag_usage_on_insert AFTER INSERT ON episode_tags
        BEGIN
            UPDATE tags 
            SET usage_count = usage_count + 1,
                last_used_at = datetime('now')
            WHERE id = new.tag_id;
        END;
    """))
    
    connection.execute(text("""
        CREATE TRIGGER update_tag_usage_on_delete AFTER DELETE ON episode_tags
        BEGIN
            UPDATE tags 
            SET usage_count = usage_count - 1
            WHERE id = old.tag_id;
        END;
    """))


def downgrade():
    """Remove FTS5 search support and enhanced tag functionality"""
    
    connection = op.get_bind()
    
    # Drop triggers
    connection.execute(text("DROP TRIGGER IF EXISTS episode_search_insert;"))
    connection.execute(text("DROP TRIGGER IF EXISTS episode_search_update;"))
    connection.execute(text("DROP TRIGGER IF EXISTS episode_search_delete;"))
    connection.execute(text("DROP TRIGGER IF EXISTS update_tag_usage_on_insert;"))
    connection.execute(text("DROP TRIGGER IF EXISTS update_tag_usage_on_delete;"))
    
    # Drop FTS5 virtual table
    connection.execute(text("DROP TABLE IF EXISTS episode_search;"))
    
    # Drop indexes
    op.drop_index('idx_episode_tags_composite', 'episode_tags')
    op.drop_index('idx_episodes_duration', 'episodes')
    op.drop_index('idx_episodes_search_composite', 'episodes')
    op.drop_index('idx_tags_color', 'tags')
    op.drop_index('idx_tags_usage_count', 'tags')
    op.drop_index('idx_tags_channel_name', 'tags')
    
    # Remove columns from tags table
    with op.batch_alter_table('tags', schema=None) as batch_op:
        batch_op.drop_column('is_system_tag')
        batch_op.drop_column('last_used_at')
        batch_op.drop_column('usage_count')
        batch_op.drop_column('color')