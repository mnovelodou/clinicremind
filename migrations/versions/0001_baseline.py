"""baseline (empty)

Establishes a stable parent revision so D1 adds the first domain tables as a new
revision on top of this one. Intentionally creates nothing.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-19

"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
