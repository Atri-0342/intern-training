"""allow uploaded analysis job status

Revision ID: bdd1f86831a2
Revises: 45b3d2213c41
Create Date: 2026-09-24 04:53:58.886546

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdd1f86831a2'
down_revision: Union[str, Sequence[str], None] = '45b3d2213c41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "analysis_jobs_status_check",
        "analysis_jobs",
        type_="check",
    )

    op.create_check_constraint(
        "analysis_jobs_status_check",
        "analysis_jobs",
        "status IN ('uploaded', 'pending', 'running', 'done', 'failed')",
    )
    
def downgrade() -> None:
    op.drop_constraint(
        "analysis_jobs_status_check",
        "analysis_jobs",
        type_="check",
    )

    op.create_check_constraint(
        "analysis_jobs_status_check",
        "analysis_jobs",
        "status IN ('pending', 'running', 'done', 'failed')",
    )
