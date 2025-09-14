"""Add logging_config table for runtime logging overrides

Revision ID: ff20250914b
Revises: ff20250914
Create Date: 2025-09-14 19:02:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff20250914b'
down_revision: Union[str, None] = 'ff20250914'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'logging_config',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('module', sa.Text(), nullable=True),  # NULL -> global override
        sa.Column('level', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index('idx_logging_config_expires', 'logging_config', ['expires_at'])


def downgrade() -> None:
    op.drop_index('idx_logging_config_expires', table_name='logging_config')
    op.drop_table('logging_config')

