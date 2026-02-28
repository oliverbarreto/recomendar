"""add_timezone_to_user_settings

Revision ID: 7f7abf5fdf3f
Revises: 7d0e08ad4b92
Create Date: 2025-12-02 00:19:12.150197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f7abf5fdf3f'
down_revision: Union[str, Sequence[str], None] = '7d0e08ad4b92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add timezone column to user_settings table"""
    # Add timezone column with default value
    op.add_column('user_settings',
        sa.Column('timezone', sa.String(length=100),
                  nullable=False,
                  server_default='Europe/Madrid')
    )


def downgrade() -> None:
    """Remove timezone column from user_settings table"""
    op.drop_column('user_settings', 'timezone')
