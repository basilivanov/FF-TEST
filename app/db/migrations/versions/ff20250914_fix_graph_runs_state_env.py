"""Fix graph_runs schema: add state_json/env and indexes

Revision ID: ff20250914
Revises: 7f3c68397d5d
Create Date: 2025-09-14 18:50:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff20250914'
down_revision: Union[str, None] = '7f3c68397d5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(inspector: sa.engine.reflection.Inspector, table: str, column: str) -> bool:
    return column in [c['name'] for c in inspector.get_columns(table)]


def _index_exists(inspector: sa.engine.reflection.Inspector, table: str, idx_name: str) -> bool:
    try:
        return idx_name in [i['name'] for i in inspector.get_indexes(table)]
    except Exception:
        # SQLite PRAGMA fallback
        conn = op.get_bind()
        res = conn.execute(sa.text(f"PRAGMA index_list('{table}')"))
        idxs = [row[1] for row in res.fetchall()]
        return idx_name in idxs


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    # graph_runs: add state_json (TEXT) if missing
    if not _column_exists(inspector, 'graph_runs', 'state_json'):
        with op.batch_alter_table('graph_runs') as batch_op:
            batch_op.add_column(sa.Column('state_json', sa.Text(), nullable=True))

    # graph_runs: add env if missing, default to 'test' for existing rows
    if not _column_exists(inspector, 'graph_runs', 'env'):
        with op.batch_alter_table('graph_runs') as batch_op:
            batch_op.add_column(sa.Column('env', sa.String(length=32), nullable=True))
        op.execute(sa.text("UPDATE graph_runs SET env='test' WHERE env IS NULL"))

    # Create helpful composite index if absent
    if not _index_exists(inspector, 'graph_runs', 'idx_graph_runs_feat_env_status'):
        op.create_index('idx_graph_runs_feat_env_status', 'graph_runs', ['feature_id', 'env', 'status'], unique=False)


def downgrade() -> None:
    # Best-effort clean downgrade
    try:
        op.drop_index('idx_graph_runs_feat_env_status', table_name='graph_runs')
    except Exception:
        pass
    with op.batch_alter_table('graph_runs') as batch_op:
        try:
            batch_op.drop_column('env')
        except Exception:
            pass
        try:
            batch_op.drop_column('state_json')
        except Exception:
            pass

