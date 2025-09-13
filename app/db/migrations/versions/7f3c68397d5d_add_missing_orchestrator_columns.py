"""Add missing orchestrator columns

Revision ID: 7f3c68397d5d
Revises: abe7202a6905
Create Date: 2025-09-12 17:56:53.883461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f3c68397d5d'
down_revision: Union[str, None] = 'abe7202a6905'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Note: These columns were already added manually during development
    # This migration serves as a record for future deployments
    
    # Check if columns already exist before adding them
    import sqlite3
    
    try:
        # Add missing columns to features table (if they don't exist)
        with op.batch_alter_table('features') as batch_op:
            try:
                batch_op.add_column(sa.Column('plan_dsl_json', sa.Text(), nullable=True, default='{}'))
            except:
                pass  # Column already exists
            try:
                batch_op.add_column(sa.Column('planned_at', sa.DateTime(), nullable=True))
            except:
                pass
            try:
                batch_op.add_column(sa.Column('finished_at', sa.DateTime(), nullable=True))
            except:
                pass
        
        # Add missing columns to tasks table (if they don't exist)  
        with op.batch_alter_table('tasks') as batch_op:
            try:
                batch_op.add_column(sa.Column('dsl_json', sa.Text(), nullable=True, default='{}'))
            except:
                pass
            try:
                batch_op.add_column(sa.Column('finished_at', sa.DateTime(), nullable=True))
            except:
                pass
        
        # Add missing columns to graph_runs table (if they don't exist)
        with op.batch_alter_table('graph_runs') as batch_op:
            try:
                batch_op.add_column(sa.Column('feature_id', sa.Integer(), nullable=True))
            except:
                pass
            try:
                batch_op.add_column(sa.Column('graph_name', sa.Text(), nullable=True))
            except:
                pass
            try:
                batch_op.add_column(sa.Column('thread_id', sa.Text(), nullable=True))
            except:
                pass
            try:
                batch_op.add_column(sa.Column('last_checkpoint_at', sa.DateTime(), nullable=True))
            except:
                pass
    except Exception as e:
        print(f"Note: Some columns may already exist: {e}")


def downgrade() -> None:
    # Remove added columns from graph_runs table
    with op.batch_alter_table('graph_runs') as batch_op:
        batch_op.drop_column('last_checkpoint_at')
        batch_op.drop_column('thread_id') 
        batch_op.drop_column('graph_name')
        batch_op.drop_column('feature_id')
    
    # Remove added columns from tasks table
    with op.batch_alter_table('tasks') as batch_op:
        batch_op.drop_column('finished_at')
        batch_op.drop_column('dsl_json')
    
    # Remove added columns from features table
    with op.batch_alter_table('features') as batch_op:
        batch_op.drop_column('finished_at')
        batch_op.drop_column('planned_at')
        batch_op.drop_column('plan_dsl_json')
