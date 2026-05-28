"""add email verification

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "email_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )
        batch_op.add_column(
            sa.Column("email_verified_at", sa.DateTime(), nullable=True)
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("email_verified", server_default=None)

    op.create_table(
        "verification_code",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "code_type",
            sa.Enum(
                "verify_email",
                "forget_password",
                "change_email",
                name="verificationcodetype",
            ),
            nullable=False,
        ),
        sa.Column(
            "code_hash",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column(
            "sent_to",
            sqlmodel.sql.sqltypes.AutoString(length=255),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_verification_code_user_id"),
        "verification_code",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verification_code_code_type"),
        "verification_code",
        ["code_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_verification_code_sent_to"),
        "verification_code",
        ["sent_to"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_verification_code_sent_to"), table_name="verification_code")
    op.drop_index(
        op.f("ix_verification_code_code_type"), table_name="verification_code"
    )
    op.drop_index(op.f("ix_verification_code_user_id"), table_name="verification_code")
    op.drop_table("verification_code")

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("email_verified_at")
        batch_op.drop_column("email_verified")
