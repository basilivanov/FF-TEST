"""Add agents_status_cache table for SWR caching

Revision ID: abe7202a6905
Revises: 2ece5b93e49c
Create Date: 2025-08-30 09:10:46.823841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abe7202a6905'
down_revision: Union[str, None] = '2ece5b93e49c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаём таблицу кэша статусов агентов для SWR политики
    op.create_table('agents_status_cache',
        sa.Column('model', sa.Text(), nullable=False),
        sa.Column('provider', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('oauth_ok', sa.Boolean(), nullable=False, default=False),
        sa.Column('tokens_used', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('checked_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('meta_json', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('model', 'provider')
    )


def downgrade() -> None:
    op.drop_table('agents_status_cache')
