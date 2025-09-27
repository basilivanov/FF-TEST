"""add gitops fields to features

Revision ID: ff001
Revises: abe7202a6905
Create Date: 2025-09-16 09:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ff001'
down_revision = 'abe7202a6905'
branch_labels = None
depends_on = None


def upgrade():
    """Add GitOps fields to features table."""
    # Add GitOps fields
    op.add_column('features', sa.Column('git_branch', sa.String(), nullable=True))
    op.add_column('features', sa.Column('pr_url', sa.String(), nullable=True))
    op.add_column('features', sa.Column('commit_sha', sa.String(), nullable=True))
    op.add_column('features', sa.Column('merged', sa.Boolean(), nullable=True))
    op.add_column('features', sa.Column('merged_sha', sa.String(), nullable=True))
    op.add_column('features', sa.Column('last_corr_id', sa.String(), nullable=True))
    op.add_column('features', sa.Column('branch_name', sa.String(), nullable=True))
    op.add_column('features', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('features', sa.Column('finished_at', sa.DateTime(), nullable=True))


def downgrade():
    """Remove GitOps fields from features table."""
    op.drop_column('features', 'finished_at')
    op.drop_column('features', 'updated_at')
    op.drop_column('features', 'branch_name')
    op.drop_column('features', 'last_corr_id')
    op.drop_column('features', 'merged_sha')
    op.drop_column('features', 'merged')
    op.drop_column('features', 'commit_sha')
    op.drop_column('features', 'pr_url')
    op.drop_column('features', 'git_branch')