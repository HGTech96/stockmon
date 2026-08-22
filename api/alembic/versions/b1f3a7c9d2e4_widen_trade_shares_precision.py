"""widen trade shares precision

Revision ID: b1f3a7c9d2e4
Revises: 32880556b9a9
Create Date: 2026-08-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f3a7c9d2e4'
down_revision: Union[str, Sequence[str], None] = '32880556b9a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "trades",
        "shares",
        type_=sa.Numeric(precision=12, scale=6),
        existing_type=sa.Numeric(precision=12, scale=4),
    )


def downgrade() -> None:
    op.alter_column(
        "trades",
        "shares",
        type_=sa.Numeric(precision=12, scale=4),
        existing_type=sa.Numeric(precision=12, scale=6),
    )
