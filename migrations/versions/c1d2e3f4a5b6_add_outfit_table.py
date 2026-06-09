"""add outfit table and event season

Revision ID: c1d2e3f4a5b6
Revises: b0c1d2e3f4a5
Create Date: 2026-06-08 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b0c1d2e3f4a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "event",
        sa.Column(
            "season",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.drop_column("event", "outfit_suggestions")
    op.drop_column("event", "outfits_generated_at")

    op.create_table(
        "outfit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("color_harmony", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("reasoning", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["event_id"], ["event.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_outfit_user_id"), "outfit", ["user_id"], unique=False)
    op.create_index(op.f("ix_outfit_event_id"), "outfit", ["event_id"], unique=False)

    op.create_table(
        "outfit_dress",
        sa.Column("outfit_id", sa.Integer(), nullable=False),
        sa.Column("dress_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["dress_id"], ["dress.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["outfit_id"], ["outfit.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("outfit_id", "dress_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("outfit_dress")
    op.drop_index(op.f("ix_outfit_event_id"), table_name="outfit")
    op.drop_index(op.f("ix_outfit_user_id"), table_name="outfit")
    op.drop_table("outfit")

    op.add_column(
        "event",
        sa.Column("outfits_generated_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "event",
        sa.Column("outfit_suggestions", sa.JSON(), nullable=True),
    )
    op.drop_column("event", "season")
