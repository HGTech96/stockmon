"""add login_attempts table

Revision ID: 91d69d85feee
Revises: a3c7b38e1f11
Create Date: 2026-09-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91d69d85feee'
down_revision: Union[str, Sequence[str], None] = 'a3c7b38e1f11'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'login_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('succeeded', sa.Boolean(), nullable=False),
    )
    op.create_index('ix_login_attempts_username', 'login_attempts', ['username'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_login_attempts_username', table_name='login_attempts')
    op.drop_table('login_attempts')
