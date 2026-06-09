"""add job notification and device_token tables

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-06-09 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("job_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(length=2000), nullable=True),
        sa.Column(
            "celery_task_id",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_celery_task_id"), "job", ["celery_task_id"], unique=False)
    op.create_index(op.f("ix_job_job_type"), "job", ["job_type"], unique=False)
    op.create_index(op.f("ix_job_status"), "job", ["status"], unique=False)
    op.create_index(op.f("ix_job_user_id"), "job", ["user_id"], unique=False)

    op.create_table(
        "device_token",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sqlmodel.sql.sqltypes.AutoString(length=512), nullable=False),
        sa.Column("platform", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(op.f("ix_device_token_token"), "device_token", ["token"], unique=True)
    op.create_index(op.f("ix_device_token_user_id"), "device_token", ["user_id"], unique=False)

    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("body", sqlmodel.sql.sqltypes.AutoString(length=1024), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notification_is_read"), "notification", ["is_read"], unique=False)
    op.create_index(op.f("ix_notification_user_id"), "notification", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_notification_user_id"), table_name="notification")
    op.drop_index(op.f("ix_notification_is_read"), table_name="notification")
    op.drop_table("notification")
    op.drop_index(op.f("ix_device_token_user_id"), table_name="device_token")
    op.drop_index(op.f("ix_device_token_token"), table_name="device_token")
    op.drop_table("device_token")
    op.drop_index(op.f("ix_job_user_id"), table_name="job")
    op.drop_index(op.f("ix_job_status"), table_name="job")
    op.drop_index(op.f("ix_job_job_type"), table_name="job")
    op.drop_index(op.f("ix_job_celery_task_id"), table_name="job")
    op.drop_table("job")
