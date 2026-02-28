"""add audio language and quality columns to episodes

Revision ID: i1j2k3l4m5n6
Revises: 36ae9abb89c6
Create Date: 2026-02-08 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i1j2k3l4m5n6'
down_revision: Union[str, None] = '36ae9abb89c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('episodes', sa.Column('audio_language', sa.String(10), nullable=True))
    op.add_column('episodes', sa.Column('audio_quality', sa.String(20), nullable=True))
    op.add_column('episodes', sa.Column('requested_language', sa.String(10), nullable=True))
    op.add_column('episodes', sa.Column('requested_quality', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('episodes', 'requested_quality')
    op.drop_column('episodes', 'requested_language')
    op.drop_column('episodes', 'audio_quality')
    op.drop_column('episodes', 'audio_language')
