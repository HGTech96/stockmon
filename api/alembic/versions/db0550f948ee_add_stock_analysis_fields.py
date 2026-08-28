"""add stock analysis fields

Revision ID: db0550f948ee
Revises: 86f945a068ae
Create Date: 2026-08-28 10:53:11.755007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db0550f948ee'
down_revision: Union[str, Sequence[str], None] = '86f945a068ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('stocks', sa.Column('analysis_date', sa.Date(), nullable=True))
    op.add_column('stocks', sa.Column('analysis_value', sa.Numeric(precision=12, scale=4), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('stocks', 'analysis_value')
    op.drop_column('stocks', 'analysis_date')
