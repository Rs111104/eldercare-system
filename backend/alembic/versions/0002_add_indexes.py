"""add useful indexes

Revision ID: 0002_add_indexes
Revises: 
Create Date: 2026-05-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_add_indexes'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade():
    # create indexes if tables exist (graceful for non-linear migrations)
    try:
        op.create_index('ix_tasks_status', 'tasks', ['status'])
    except Exception:
        pass
    try:
        op.create_index('ix_tasks_worker_id', 'tasks', ['worker_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_tracking_task_id', 'tracking', ['task_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_payouts_worker_id', 'payouts', ['worker_id'])
    except Exception:
        pass
    try:
        op.create_index('ix_whatsapp_processed', 'whatsapp_messages', ['processed'])
    except Exception:
        pass


def downgrade():
    op.drop_index('ix_whatsapp_processed', table_name='whatsapp_messages')
    op.drop_index('ix_payouts_worker_id', table_name='payouts')
    op.drop_index('ix_tracking_task_id', table_name='tracking')
    op.drop_index('ix_tasks_worker_id', table_name='tasks')
    op.drop_index('ix_tasks_status', table_name='tasks')
