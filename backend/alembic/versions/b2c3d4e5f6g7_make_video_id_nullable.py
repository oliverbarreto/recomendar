"""Make video_id nullable for uploaded episodes

Revision ID: b2c3d4e5f6g7
Revises: a1b2c3d4e5f6
Create Date: 2025-10-18 15:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6g7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # SQLite doesn't support ALTER COLUMN directly, so we need to:
    # 1. Create a new table with the correct schema
    # 2. Copy data
    # 3. Drop old table
    # 4. Rename new table
    
    # However, since we're using SQLAlchemy with SQLite, we can use batch operations
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.alter_column('video_id',
                              existing_type=sa.String(length=20),
                              nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Make video_id NOT NULL again
    # First, we need to ensure all NULL values have a placeholder
    op.execute("UPDATE episodes SET video_id = 'uploaded' WHERE video_id IS NULL")
    
    with op.batch_alter_table('episodes', schema=None) as batch_op:
        batch_op.alter_column('video_id',
                              existing_type=sa.String(length=20),
                              nullable=False)



