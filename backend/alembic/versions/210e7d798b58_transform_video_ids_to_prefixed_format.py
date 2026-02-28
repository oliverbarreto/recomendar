"""transform_video_ids_to_prefixed_format

Transform video_ids from raw format to prefixed format:
- YouTube episodes: "dQw4w9WgXcQ" → "yt_dQw4w9WgXcQ"
- Uploaded episodes: NULL → "up_<generated_id>"

This migration also:
- Makes video_id NOT NULL (reverts b2c3d4e5f6g7)
- Changes column length from 20 to 14 characters
- Adds CHECK constraint for prefix validation

Revision ID: 210e7d798b58
Revises: b2c3d4e5f6g7
Create Date: 2025-10-22 20:18:15.597273

"""
from typing import Sequence, Union
import secrets
import string

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '210e7d798b58'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def generate_upload_id() -> str:
    """Generate a random 11-character alphanumeric ID for uploaded episodes"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(11))


def upgrade() -> None:
    """Upgrade schema: Transform video_ids to prefixed format"""

    # Step 1: Get database connection
    connection = op.get_bind()

    # Step 2: Transform existing YouTube episodes (add yt_ prefix)
    # Only update episodes that have a non-NULL video_id and source_type='youtube'
    connection.execute(text("""
        UPDATE episodes
        SET video_id = 'yt_' || video_id
        WHERE video_id IS NOT NULL
          AND source_type = 'youtube'
          AND length(video_id) = 11
          AND video_id NOT LIKE 'yt_%'
          AND video_id NOT LIKE 'up_%'
    """))

    # Step 3: Generate unique up_* IDs for uploaded episodes (those with NULL video_id)
    # Get all episodes with NULL video_id
    result = connection.execute(text("""
        SELECT id FROM episodes
        WHERE video_id IS NULL
          AND source_type = 'upload'
    """))

    null_video_id_episodes = result.fetchall()

    # Generate and assign unique up_* IDs
    for episode_row in null_video_id_episodes:
        episode_id = episode_row[0]
        upload_id = f"up_{generate_upload_id()}"

        # Update episode with generated ID
        connection.execute(
            text("UPDATE episodes SET video_id = :video_id WHERE id = :id"),
            {"video_id": upload_id, "id": episode_id}
        )

    # Step 4: Use batch operations for SQLite-compatible schema changes
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        # Change column to NOT NULL and adjust length
        batch_op.alter_column('video_id',
                              existing_type=sa.String(length=20),
                              type_=sa.String(length=14),
                              nullable=False)

    # Step 5: Add CHECK constraint to enforce prefix format
    # SQLite supports CHECK constraints added via CREATE TABLE or ALTER TABLE ADD CONSTRAINT
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.create_check_constraint(
            'ck_episode_video_id_prefix',
            "video_id LIKE 'yt_%' OR video_id LIKE 'up_%'"
        )

    print(f"✅ Migration complete: Transformed {len(null_video_id_episodes)} uploaded episodes")


def downgrade() -> None:
    """Downgrade schema: Revert prefixed video_ids to original format"""

    # Step 1: Get database connection
    connection = op.get_bind()

    # Step 2: Remove CHECK constraint
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.drop_constraint('ck_episode_video_id_prefix', type_='check')

    # Step 3: Strip yt_ prefix from YouTube episodes
    connection.execute(text("""
        UPDATE episodes
        SET video_id = substr(video_id, 4)
        WHERE video_id LIKE 'yt_%'
    """))

    # Step 4: Set uploaded episodes (up_*) back to NULL
    connection.execute(text("""
        UPDATE episodes
        SET video_id = NULL
        WHERE video_id LIKE 'up_%'
    """))

    # Step 5: Make video_id nullable again and revert column length
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.alter_column('video_id',
                              existing_type=sa.String(length=14),
                              type_=sa.String(length=20),
                              nullable=True)

    print("✅ Downgrade complete: Reverted video_ids to original format")
