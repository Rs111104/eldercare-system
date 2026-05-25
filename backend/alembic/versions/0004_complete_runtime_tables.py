"""complete runtime tables

Revision ID: 0004_complete_runtime_tables
Revises: 0003_add_refresh_token_role
Create Date: 2026-05-25 21:15:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_complete_runtime_tables"
down_revision = "0003_add_refresh_token_role"
branch_labels = None
depends_on = None


def _add_column_if_missing(table_name: str, column: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {item["name"] for item in inspector.get_columns(table_name)}
    if column.name not in existing:
        op.add_column(table_name, column)


def _create_table_if_missing(table_name: str, *columns: sa.Column) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        op.create_table(table_name, *columns)


def upgrade():
    _add_column_if_missing("tasks", sa.Column("completed_at", sa.String(), nullable=True))
    _add_column_if_missing("tasks", sa.Column("cancellation_reason", sa.Text(), nullable=True))

    _create_table_if_missing(
        "tracking",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=True),
        sa.Column("timestamp", sa.String(), nullable=True),
    )
    _create_table_if_missing(
        "payouts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("split_type", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("verification_available_at", sa.String(), nullable=True),
        sa.Column("released_at", sa.String(), nullable=True),
    )
    _create_table_if_missing(
        "pricing_config",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("service_type", sa.String(), nullable=True, unique=True),
        sa.Column("base_price", sa.Float(), nullable=True),
        sa.Column("per_km_rate", sa.Float(), nullable=True),
        sa.Column("updated_at", sa.String(), nullable=True),
    )


def downgrade():
    for table_name in ("pricing_config", "payouts", "tracking"):
        try:
            op.drop_table(table_name)
        except Exception:
            pass
    for column_name in ("cancellation_reason", "completed_at"):
        try:
            op.drop_column("tasks", column_name)
        except Exception:
            pass
