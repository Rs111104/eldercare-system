"""add useful indexes

Revision ID: 0002_add_indexes
Revises: 
Create Date: 2026-05-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '0002_add_indexes'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def _has_table(table_name):
    return table_name in sa.inspect(op.get_bind()).get_table_names()


def _has_index(table_name, index_name):
    indexes = sa.inspect(op.get_bind()).get_indexes(table_name)
    return any(index["name"] == index_name for index in indexes)


def _create_index(table_name, index_name, columns):
    if _has_table(table_name) and not _has_index(table_name, index_name):
        op.create_index(index_name, table_name, columns)


def upgrade():
    _create_index('tasks', 'ix_tasks_status', ['status'])
    _create_index('tasks', 'ix_tasks_worker_id', ['worker_id'])
    _create_index('tracking', 'ix_tracking_task_id', ['task_id'])
    _create_index('payouts', 'ix_payouts_worker_id', ['worker_id'])
    _create_index('whatsapp_messages', 'ix_whatsapp_processed', ['processed'])


def downgrade():
    for table_name, index_name in (
        ('whatsapp_messages', 'ix_whatsapp_processed'),
        ('payouts', 'ix_payouts_worker_id'),
        ('tracking', 'ix_tracking_task_id'),
        ('tasks', 'ix_tasks_worker_id'),
        ('tasks', 'ix_tasks_status'),
    ):
        if _has_table(table_name) and _has_index(table_name, index_name):
            op.drop_index(index_name, table_name=table_name)
