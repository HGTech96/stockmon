from datetime import datetime, timezone
from decimal import Decimal

from stockmon.db.models import ScreenerResult

SCREENER_TOP_KEYS = {"meta", "runAt", "results"}
SCREENER_RESULT_KEYS = {
    "ticker", "companyName", "currentPrice", "change1dPct", "suggestion",
    "metCount", "totalCount", "rsi", "priceVs30dAvgPct", "sharpMove", "status",
}


def test_screener_never_run_is_empty_state(client) -> None:
    r = client.get("/api/screener")
    assert r.status_code == 200
    body = r.json()
    assert set(body.keys()) == SCREENER_TOP_KEYS
    assert body["runAt"] is None
    assert body["results"] == []


def test_screener_returns_latest_run_rows(client, db) -> None:
    run_at = datetime(2026, 8, 19, 9, 12, tzinfo=timezone.utc)
    db.add(
        ScreenerResult(
            ticker="PLTR",
            company_name="Palantir Technologies Inc.",
            current_price=Decimal("27.85"),
            change_1d_pct=Decimal("1.52"),
            status="ok",
            suggestion="BUY",
            conditions_met=3,
            conditions_total=4,
            rsi=Decimal("38.00"),
            price_vs_30d_avg_pct=Decimal("-4.10"),
            sharp_move=False,
            run_at=run_at,
        )
    )
    db.commit()

    r = client.get("/api/screener")
    assert r.status_code == 200
    body = r.json()
    assert body["runAt"] is not None
    assert len(body["results"]) == 1

    row = body["results"][0]
    assert set(row.keys()) == SCREENER_RESULT_KEYS
    assert row["ticker"] == "PLTR"
    assert row["companyName"] == "Palantir Technologies Inc."
    assert row["currentPrice"] == 27.85
    assert row["change1dPct"] == 1.52
    assert row["suggestion"] == "BUY"
    assert row["metCount"] == 3
    assert row["totalCount"] == 4
    assert row["rsi"] == 38.0
    assert row["priceVs30dAvgPct"] == -4.1
    assert row["sharpMove"] is False
    assert row["status"] == "ok"


def test_screener_insufficient_history_row_has_null_indicators(client, db) -> None:
    run_at = datetime(2026, 8, 19, 9, 12, tzinfo=timezone.utc)
    db.add(
        ScreenerResult(
            ticker="NEWCO",
            company_name="Newco Inc.",
            current_price=Decimal("5.00"),
            change_1d_pct=Decimal("0.00"),
            status="insufficient_history",
            suggestion=None,
            conditions_met=None,
            conditions_total=None,
            rsi=None,
            price_vs_30d_avg_pct=None,
            sharp_move=None,
            run_at=run_at,
        )
    )
    db.commit()

    body = client.get("/api/screener").json()
    row = body["results"][0]
    assert row["status"] == "insufficient_history"
    assert row["suggestion"] is None
    assert row["rsi"] is None
    assert row["sharpMove"] is None
