"""add socks category

Revision ID: c3d4e5f6a7b8
Revises: b2e3f4a5c6d7
Create Date: 2026-05-20 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2e3f4a5c6d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CATEGORY_VALUES = (
    "top",
    "bottom",
    "outerwear",
    "shoes",
    "accessory",
    "dress",
    "underwear",
    "bag",
    "hat",
    "socks",
    "other",
)


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("dress", schema=None) as batch_op:
        batch_op.alter_column(
            "category",
            existing_type=sa.Enum(*_CATEGORY_VALUES[:-1], name="category"),
            type_=sa.Enum(*_CATEGORY_VALUES, name="category"),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("dress", schema=None) as batch_op:
        batch_op.alter_column(
            "category",
            existing_type=sa.Enum(*_CATEGORY_VALUES, name="category"),
            type_=sa.Enum(*_CATEGORY_VALUES[:-1], name="category"),
            existing_nullable=True,
        )
