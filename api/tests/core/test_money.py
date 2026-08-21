from datetime import date
from decimal import Decimal

from stockmon.core.cash import CashFlowEvent
from stockmon.core.money import compute_money_summary


def _deposit(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="deposit", amount=Decimal(amount), date=day)


def _withdraw(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="withdraw", amount=Decimal(amount), date=day)


def _buy(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="buy", amount=Decimal(amount), date=day)


def _sell(amount: str, day: date) -> CashFlowEvent:
    return CashFlowEvent(kind="sell", amount=Decimal(amount), date=day)


def test_cash_available_and_net_deposited() -> None:
    events = [
        _deposit("1000", date(2026, 1, 1)),
        _withdraw("200", date(2026, 1, 2)),
        _buy("300", date(2026, 1, 3)),
        _sell("100", date(2026, 1, 4)),
    ]
    summary = compute_money_summary(events, realized_pnls=[], open_position_pnls=[])

    assert summary.cash_available == Decimal(1000 - 200 - 300 + 100)
    assert summary.net_deposited == Decimal(1000 - 200)


def test_realized_earned_and_lost_split_by_sign() -> None:
    summary = compute_money_summary(
        cash_flow_events=[],
        realized_pnls=[Decimal(50), Decimal(-20), Decimal(30), Decimal(-10)],
        open_position_pnls=[],
    )
    assert summary.realized_earned == Decimal(80)
    assert summary.realized_lost == Decimal(30)


def test_unrealized_gain_and_loss_split_by_sign() -> None:
    summary = compute_money_summary(
        cash_flow_events=[],
        realized_pnls=[],
        open_position_pnls=[Decimal(40), Decimal(-15), Decimal(-5)],
    )
    assert summary.unrealized_gain_open == Decimal(40)
    assert summary.unrealized_loss_open == Decimal(20)


def test_no_activity_is_all_zero() -> None:
    summary = compute_money_summary([], [], [])
    assert summary.cash_available == Decimal(0)
    assert summary.net_deposited == Decimal(0)
    assert summary.realized_earned == Decimal(0)
    assert summary.realized_lost == Decimal(0)
    assert summary.unrealized_gain_open == Decimal(0)
    assert summary.unrealized_loss_open == Decimal(0)


def test_consistency_identity_holds_across_a_scripted_sequence() -> None:
    """cashAvailable + currentValueOfHoldings ==
    netDeposited + realizedEarned - realizedLost
    + unrealizedGainOpen - unrealizedLossOpen

    Scripted sequence: deposit 1000, buy 10@50 (=500, still open, now worth
    60 -> unrealized gain 100), buy 5@80 (=400, still open, now worth 70 ->
    unrealized loss 50), sell (a different, already-closed lot) for a
    realized gain of 30 and a realized loss of 10.
    """
    cash_flow_events = [
        _deposit("1000", date(2026, 1, 1)),
        _buy("500", date(2026, 1, 2)),  # 10 shares @ 50, current value 600 (open)
        _buy("400", date(2026, 1, 3)),  # 5 shares @ 80, current value 350 (open)
        _buy("100", date(2026, 1, 4)),  # closed lot, bought for 100
        _sell("130", date(2026, 1, 5)),  # ... sold for 130 -> realized +30
        _buy("50", date(2026, 1, 6)),  # closed lot, bought for 50
        _sell("40", date(2026, 1, 7)),  # ... sold for 40 -> realized -10
    ]
    realized_pnls = [Decimal(30), Decimal(-10)]
    open_position_pnls = [Decimal(100), Decimal(-50)]  # 600-500, 350-400
    current_value_of_holdings = Decimal(600) + Decimal(350)

    summary = compute_money_summary(cash_flow_events, realized_pnls, open_position_pnls)

    left = summary.cash_available + current_value_of_holdings
    right = (
        summary.net_deposited
        + summary.realized_earned
        - summary.realized_lost
        + summary.unrealized_gain_open
        - summary.unrealized_loss_open
    )
    assert left == right
