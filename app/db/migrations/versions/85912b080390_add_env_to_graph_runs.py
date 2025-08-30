"""add env to graph_runs

Revision ID: 85912b080390
Revises: a1b2c3d4e5f0
Create Date: 2025-08-25 16:30:26.124709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85912b080390'
down_revision: Union[str, None] = 'a1b2c3d4e5f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Проверим, существует ли уже нужный индекс
    connection = op.get_bind()
    result = connection.execute(sa.text("PRAGMA index_list('graph_runs')"))
    indexes = [row[1] for row in result.fetchall()]
    
    # Создаем индекс, если его ещё нет
    if 'idx_graph_runs_feat_env_status' not in indexes:
        op.create_index('idx_graph_runs_feat_env_status', 'graph_runs', ['feature_id', 'env', 'status'], unique=False)


def downgrade() -> None:
    # Проверим, существует ли индекс перед удалением
    connection = op.get_bind()
    result = connection.execute(sa.text("PRAGMA index_list('graph_runs')"))
    indexes = [row[1] for row in result.fetchall()]
    
    # Удаляем индекс, если он существует
    if 'idx_graph_runs_feat_env_status' in indexes:
        op.drop_index('idx_graph_runs_feat_env_status', table_name='graph_runs')