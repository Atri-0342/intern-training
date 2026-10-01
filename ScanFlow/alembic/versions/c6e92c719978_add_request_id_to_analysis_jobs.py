"""add request id to analysis jobs

Revision ID: c6e92c719978
Revises: bdd1f86831a2
Create Date: 2026-10-01 21:55:12.539073

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6e92c719978'
down_revision: Union[str, Sequence[str], None] = 'bdd1f86831a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "analysis_jobs",
        sa.Column("request_id", sa.TEXT(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column(
        "analysis_jobs",
        "request_id",
    )
