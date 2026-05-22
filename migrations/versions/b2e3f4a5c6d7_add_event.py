"""add event

Revision ID: b2e3f4a5c6d7
Revises: a1f2c3d4e5f6
Create Date: 2026-05-20 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "b2e3f4a5c6d7"
down_revision: Union[str, Sequence[str], None] = "a1f2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "event",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "title",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            "event_type",
            sa.Enum(
                "business",
                "casual",
                "smart_casual",
                "formal",
                "outdoor",
                "party",
                "sports",
                "date_night",
                "other",
                name="eventtype",
            ),
            nullable=False,
        ),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column(
            "city",
            sa.Enum(
                "berlin",
                "munich",
                "hamburg",
                "cologne",
                "frankfurt",
                "stuttgart",
                "dusseldorf",
                "leipzig",
                "dresden",
                "nuremberg",
                "bremen",
                "hannover",
                "dortmund",
                "essen",
                "mannheim",
                name="germancity",
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("outfit_suggestions", sa.JSON(), nullable=True),
        sa.Column("outfits_generated_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_event_user_id"), "event", ["user_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_event_user_id"), table_name="event")
    op.drop_table("event")
