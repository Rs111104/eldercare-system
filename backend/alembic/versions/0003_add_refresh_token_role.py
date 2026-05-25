"""add role column to refresh_tokens

Revision ID: 0003_add_refresh_token_role
Revises: 0002_add_indexes
Create Date: 2026-05-25 20:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0003_add_refresh_token_role'
down_revision = '0002_add_indexes'
branch_labels = None
depends_on = None


def upgrade():
    # Add `role` column if it doesn't exist already.
    try:
        op.add_column('refresh_tokens', sa.Column('role', sa.String(), nullable=True))
    except Exception:
        pass


def downgrade():
    try:
        op.drop_column('refresh_tokens', 'role')
    except Exception:
        pass
