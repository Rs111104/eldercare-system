"""add role column to refresh_tokens

Revision ID: 0003_add_refresh_token_role
Revises: 0002_add_indexes
Create Date: 2026-05-25 20:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_add_refresh_token_role'
down_revision = '0002_add_indexes'
branch_labels = None
depends_on = None


def _has_column(table_name, column_name):
    columns = sa.inspect(op.get_bind()).get_columns(table_name)
    return any(column["name"] == column_name for column in columns)


def upgrade():
    if not _has_column('refresh_tokens', 'role'):
        op.add_column('refresh_tokens', sa.Column('role', sa.String(), nullable=True))


def downgrade():
    if _has_column('refresh_tokens', 'role'):
        op.drop_column('refresh_tokens', 'role')
