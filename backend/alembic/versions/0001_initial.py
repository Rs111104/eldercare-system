"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('phone', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('user_type', sa.String(), nullable=False),
        sa.Column('extra', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
    )

    op.create_table(
        'tasks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String()),
        sa.Column('customer_id', sa.String()),
        sa.Column('worker_id', sa.String()),
        sa.Column('service_type', sa.String()),
        sa.Column('status', sa.String()),
        sa.Column('description', sa.Text()),
        sa.Column('price', sa.Float()),
        sa.Column('urgency', sa.Float()),
        sa.Column('created_at', sa.String(), nullable=True),
    )

    op.create_table(
        'whatsapp_messages',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('phone', sa.String()),
        sa.Column('direction', sa.String()),
        sa.Column('message_type', sa.String()),
        sa.Column('content', sa.Text()),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('timestamp', sa.String(), nullable=True),
    )

    op.create_table(
        'refresh_tokens',
        sa.Column('token', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('expires_at', sa.String(), nullable=True),
    )


def downgrade():
    op.drop_table('refresh_tokens')
    op.drop_table('whatsapp_messages')
    op.drop_table('tasks')
    op.drop_table('users')
