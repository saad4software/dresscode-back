"""add dress and media

Revision ID: a1f2c3d4e5f6
Revises: e36451012bcc
Create Date: 2026-05-20 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "a1f2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "e36451012bcc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "dress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "item_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=True,
        ),
        sa.Column(
            "category",
            sa.Enum(
                "top",
                "bottom",
                "outerwear",
                "shoes",
                "accessory",
                "dress",
                "underwear",
                "bag",
                "hat",
                "other",
                name="category",
            ),
            nullable=True,
        ),
        sa.Column("colors", sa.JSON(), nullable=False),
        sa.Column(
            "dominant_color",
            sqlmodel.sql.sqltypes.AutoString(length=7),
            nullable=True,
        ),
        sa.Column(
            "warmth_level",
            sa.Enum("light", "medium", "heavy", name="warmthlevel"),
            nullable=True,
        ),
        sa.Column("season_suitability", sa.JSON(), nullable=False),
        sa.Column("style", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "layering",
            sa.Enum("base", "mid", "outer", name="layering"),
            nullable=True,
        ),
        sa.Column(
            "pattern",
            sa.Enum(
                "solid", "striped", "plaid", "floral", "graphic", "other",
                name="pattern",
            ),
            nullable=True,
        ),
        sa.Column(
            "material",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column(
            "formality",
            sa.Enum(
                "casual", "smart_casual", "business", "formal", name="formality"
            ),
            nullable=True,
        ),
        sa.Column(
            "brightness",
            sa.Enum("light", "dark", "mixed", name="brightness"),
            nullable=True,
        ),
        sa.Column("water_resistant", sa.Boolean(), nullable=False),
        sa.Column("occasion_tags", sa.JSON(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "ready", "needs_review", name="dressstatus"),
            nullable=False,
        ),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column(
            "ai_model_version",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
        sa.Column("ai_processed_at", sa.DateTime(), nullable=True),
        sa.Column("is_archived", sa.Boolean(), nullable=False),
        sa.Column("user_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_dress_user_id"), "dress", ["user_id"], unique=False)

    op.create_table(
        "media",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("dress_id", sa.Integer(), nullable=True),
        sa.Column(
            "storage_path",
            sqlmodel.sql.sqltypes.AutoString(length=512),
            nullable=False,
        ),
        sa.Column(
            "original_filename",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "mime_type",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column(
            "processing_status",
            sa.Enum(
                "pending", "processing", "completed", "failed",
                name="processingstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "processing_error",
            sqlmodel.sql.sqltypes.AutoString(length=512),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["dress_id"], ["dress.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_media_user_id"), "media", ["user_id"], unique=False)
    op.create_index(op.f("ix_media_dress_id"), "media", ["dress_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_media_dress_id"), table_name="media")
    op.drop_index(op.f("ix_media_user_id"), table_name="media")
    op.drop_table("media")
    op.drop_index(op.f("ix_dress_user_id"), table_name="dress")
    op.drop_table("dress")
