"""drop otp_requests table

Revision ID: b7c1f2a3d4e5
Revises: 35b4e713b0af
Create Date: 2026-05-16

"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = "b7c1f2a3d4e5"
down_revision: Union[str, Sequence[str], None] = "35b4e713b0af"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "otp_requests" in inspector.get_table_names():
        op.drop_table("otp_requests")


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = inspect(bind)
    if "otp_requests" in inspector.get_table_names():
        return

    op.create_table(
        "otp_requests",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("salt", sa.String(length=255), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
