"""add profile and personal styles

Revision ID: f7a8b9c0d1e2
Revises: 1ae2c27b40b7
Create Date: 2026-06-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "f7a8b9c0d1e2"
down_revision: Union[str, Sequence[str], None] = "1ae2c27b40b7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "personal_style",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "slug",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_personal_style_slug"), "personal_style", ["slug"], unique=True
    )

    op.create_table(
        "profile",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column(
            "gender",
            sa.Enum(
                "male",
                "female",
                "non_binary",
                "prefer_not_to_say",
                name="gender",
            ),
            nullable=True,
        ),
        sa.Column("city_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["city.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(op.f("ix_profile_city_id"), "profile", ["city_id"], unique=False)

    op.create_table(
        "profile_personal_style",
        sa.Column("profile_user_id", sa.Integer(), nullable=False),
        sa.Column("personal_style_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["personal_style_id"], ["personal_style.id"]),
        sa.ForeignKeyConstraint(["profile_user_id"], ["profile.user_id"]),
        sa.PrimaryKeyConstraint("profile_user_id", "personal_style_id"),
    )

    personal_style_table = sa.table(
        "personal_style",
        sa.column("slug", sa.String),
        sa.column("display_name", sa.String),
        sa.column("description", sa.String),
    )
    op.bulk_insert(
        personal_style_table,
        [
            {
                "slug": "classic",
                "display_name": "Classic",
                "description": "Timeless, tailored pieces and neutral palettes.",
            },
            {
                "slug": "minimalist",
                "display_name": "Minimalist",
                "description": "Clean lines, muted colors, and low visual noise.",
            },
            {
                "slug": "bold",
                "display_name": "Bold",
                "description": "Strong colors, contrast, and statement pieces.",
            },
            {
                "slug": "elegant",
                "display_name": "Elegant",
                "description": "Polished, refined, and understated luxury.",
            },
            {
                "slug": "casual",
                "display_name": "Casual",
                "description": "Relaxed, comfortable, everyday ease.",
            },
            {
                "slug": "streetwear",
                "display_name": "Streetwear",
                "description": "Urban influence with sneakers, hoodies, and layered looks.",
            },
            {
                "slug": "preppy",
                "display_name": "Preppy",
                "description": "Collegiate, crisp tailoring, stripes, and loafers.",
            },
            {
                "slug": "bohemian",
                "display_name": "Bohemian",
                "description": "Flowy silhouettes, earthy tones, and artistic layering.",
            },
            {
                "slug": "romantic",
                "display_name": "Romantic",
                "description": "Soft details, delicate fabrics, and gentle palettes.",
            },
            {
                "slug": "edgy",
                "display_name": "Edgy",
                "description": "Dark tones, leather, asymmetry, and rock-inspired edge.",
            },
            {
                "slug": "sporty",
                "display_name": "Sporty",
                "description": "Athleisure and activewear blended into daily outfits.",
            },
            {
                "slug": "vintage",
                "display_name": "Vintage",
                "description": "Retro eras, nostalgic silhouettes, and thrift aesthetic.",
            },
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("profile_personal_style")
    op.drop_index(op.f("ix_profile_city_id"), table_name="profile")
    op.drop_table("profile")
    op.drop_index(op.f("ix_personal_style_slug"), table_name="personal_style")
    op.drop_table("personal_style")
    sa.Enum(name="gender").drop(op.get_bind(), checkfirst=True)
