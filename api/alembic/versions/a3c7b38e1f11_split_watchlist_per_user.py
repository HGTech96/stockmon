"""split stocks into shared tickers + per-user watchlist_entries; per-user
settings/refresh_status; user_id on cash_events

Revision ID: a3c7b38e1f11
Revises: ae5a991032b1
Create Date: 2026-09-04 00:00:00.000000

Requires at least one row in `users` before running -- run
`python scripts/create_user.py` first (see
docs/planning/phase-23-multi-user-accounts.md). Every pre-existing row
(single implicit user before this phase) is assigned to the first account
found. Data-migrating revision; downgrade is not supported.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c7b38e1f11'
down_revision: Union[str, Sequence[str], None] = 'ae5a991032b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    target_user_id = bind.execute(sa.text("SELECT id FROM users ORDER BY id LIMIT 1")).scalar()
    if target_user_id is None:
        raise RuntimeError(
            "No user exists yet -- run `python scripts/create_user.py` to create the first "
            "account before running this migration."
        )

    # 1. stocks -> tickers (shared market-data identity)
    op.rename_table('stocks', 'tickers')

    # 2. watchlist_entries (new; per-user link to a shared ticker)
    op.create_table(
        'watchlist_entries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('ticker_id', sa.Integer(), sa.ForeignKey('tickers.id'), nullable=False),
        sa.Column('analysis_date', sa.Date(), nullable=True),
        sa.Column('analysis_value', sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'ticker_id', name='uq_watchlist_entry_user_ticker'),
    )
    op.create_index('ix_watchlist_entries_user_id', 'watchlist_entries', ['user_id'])
    op.create_index('ix_watchlist_entries_ticker_id', 'watchlist_entries', ['ticker_id'])

    op.execute(
        sa.text(
            "INSERT INTO watchlist_entries (user_id, ticker_id, analysis_date, analysis_value) "
            "SELECT :user_id, id, analysis_date, analysis_value FROM tickers"
        ).bindparams(user_id=target_user_id)
    )

    op.drop_column('tickers', 'analysis_date')
    op.drop_column('tickers', 'analysis_value')

    # 3. daily_prices.stock_id -> ticker_id (rename only; same target table)
    op.alter_column('daily_prices', 'stock_id', new_column_name='ticker_id')
    op.execute("ALTER TABLE daily_prices RENAME CONSTRAINT uq_daily_price_stock_date TO uq_daily_price_ticker_date")
    op.execute("ALTER INDEX ix_daily_prices_stock_id RENAME TO ix_daily_prices_ticker_id")
    op.execute("ALTER TABLE daily_prices RENAME CONSTRAINT daily_prices_stock_id_fkey TO daily_prices_ticker_id_fkey")

    # 4. trades.stock_id -> watchlist_entry_id
    op.add_column('trades', sa.Column('watchlist_entry_id', sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE trades SET watchlist_entry_id = we.id "
            "FROM watchlist_entries we "
            "WHERE trades.stock_id = we.ticker_id AND we.user_id = :user_id"
        ).bindparams(user_id=target_user_id)
    )
    op.drop_constraint('trades_stock_id_fkey', 'trades', type_='foreignkey')
    op.drop_index('ix_trades_stock_id', table_name='trades')
    op.drop_column('trades', 'stock_id')
    op.alter_column('trades', 'watchlist_entry_id', nullable=False)
    op.create_foreign_key(
        'trades_watchlist_entry_id_fkey', 'trades', 'watchlist_entries', ['watchlist_entry_id'], ['id']
    )
    op.create_index('ix_trades_watchlist_entry_id', 'trades', ['watchlist_entry_id'])

    # 5. profit_targets.stock_id -> watchlist_entry_id (PK)
    op.add_column('profit_targets', sa.Column('watchlist_entry_id', sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE profit_targets SET watchlist_entry_id = we.id "
            "FROM watchlist_entries we "
            "WHERE profit_targets.stock_id = we.ticker_id AND we.user_id = :user_id"
        ).bindparams(user_id=target_user_id)
    )
    op.drop_constraint('profit_targets_pkey', 'profit_targets', type_='primary')
    op.drop_constraint('profit_targets_stock_id_fkey', 'profit_targets', type_='foreignkey')
    op.drop_column('profit_targets', 'stock_id')
    op.alter_column('profit_targets', 'watchlist_entry_id', nullable=False)
    op.create_primary_key('profit_targets_pkey', 'profit_targets', ['watchlist_entry_id'])
    op.create_foreign_key(
        'profit_targets_watchlist_entry_id_fkey',
        'profit_targets',
        'watchlist_entries',
        ['watchlist_entry_id'],
        ['id'],
    )

    # 6. cash_events: add user_id
    op.add_column('cash_events', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE cash_events SET user_id = :user_id").bindparams(user_id=target_user_id))
    op.alter_column('cash_events', 'user_id', nullable=False)
    op.create_foreign_key('cash_events_user_id_fkey', 'cash_events', 'users', ['user_id'], ['id'])
    op.create_index('ix_cash_events_user_id', 'cash_events', ['user_id'])

    # 7. settings: singleton id=1 -> user_id PK
    op.add_column('settings', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE settings SET user_id = :user_id").bindparams(user_id=target_user_id))
    op.drop_constraint('settings_pkey', 'settings', type_='primary')
    op.drop_column('settings', 'id')
    op.alter_column('settings', 'user_id', nullable=False)
    op.create_primary_key('settings_pkey', 'settings', ['user_id'])
    op.create_foreign_key('settings_user_id_fkey', 'settings', 'users', ['user_id'], ['id'])

    # 8. refresh_status: singleton id=1 -> user_id PK
    op.add_column('refresh_status', sa.Column('user_id', sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE refresh_status SET user_id = :user_id").bindparams(user_id=target_user_id))
    op.drop_constraint('refresh_status_pkey', 'refresh_status', type_='primary')
    op.drop_column('refresh_status', 'id')
    op.alter_column('refresh_status', 'user_id', nullable=False)
    op.create_primary_key('refresh_status_pkey', 'refresh_status', ['user_id'])
    op.create_foreign_key('refresh_status_user_id_fkey', 'refresh_status', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    raise NotImplementedError("Downgrade not supported for this data-migrating revision.")
