# stockmon — Product Spec (original brief)

A small personal stock buy/sell helper application.

## Context

- I am not a financial specialist, so explanations must be simple and practical.
- I have around $2,000 total capital.
- I follow a predefined set of stocks (under 20).
- I am interested in relatively small gains as well. For example, I may consider selling when profit reaches roughly $30–50, depending on the position.
- I do not want automated trading.
- I do not want AI integrated into the product.
- The application should help me evaluate the situation, but the final decision must always be made by the user.

## Core Product Idea

For each stock, the application should analyze recent market data and produce a simple suggestion:

- POSSIBLE BUY
- WAIT
- POSSIBLE SELL

The suggestion should never be shown alone.

The application must also clearly show all the individual indicators used to reach that suggestion, so the user can understand the reasoning and make their own decision.

Think of it as:

Suggestion → explanation → raw indicators → user makes final decision

## Time Horizon

This is mainly a short-term decision helper.

The analysis should focus primarily on:

- Current day
- Last 7 days
- Last 30 days

It is not intended to predict long-term company performance.

## Indicators to Consider

For every stock, show at least:

1. Current price
2. 1-day price change
3. 7-day price change
4. 30-day average price
5. 30-day high
6. 30-day low
7. Distance from the 30-day high
8. Distance from the 30-day low
9. RSI
10. Current trading volume
11. Average recent trading volume
12. Current volume compared with average volume

### RSI interpretation

Use RSI as one signal, not as a direct buy/sell command.

Simple interpretation:

- RSI below 30 → potentially oversold
- RSI 30–40 → relatively weak
- RSI 40–60 → neutral
- RSI 60–70 → relatively strong
- RSI above 70 → potentially overbought

Important:

RSI < 30 must NOT automatically mean BUY.
RSI > 70 must NOT automatically mean SELL.

RSI should be evaluated together with price position, trend and volume.

## News

No AI news analysis.

Instead, the application provides useful links where the user can manually check recent news before making a decision:

- Yahoo Finance news for the stock
- Google Finance
- Company investor relations page

The application should remind the user that unusual price movement can be caused by important company news that technical indicators alone cannot explain.

## Portfolio / Selling Logic

The application knows the user's existing positions.

For each position:

- Stock
- Number of shares
- Average purchase price
- Amount invested
- Current value
- Current profit/loss in dollars
- Current profit/loss percentage

The user may define a simple desired profit target (e.g. approximately $30–50).

The application displays both dollar profit and percentage return, because $40 profit can mean very different things depending on the position size.

## Important Product Principles

1. Do not pretend the system can predict stocks reliably.
2. Do not make automatic trades.
3. Do not hide the reasoning behind the suggestion.
4. Avoid black-box scoring where possible.
5. Every recommendation should be explainable using visible indicators.
6. The user should always be able to disagree with the application's suggestion.
7. Keep terminology understandable for someone without professional finance knowledge.
8. Keep the MVP relatively simple.

## Decisions made during MVP definition (summary)

- Two separate evaluations: entry (watched stocks → BUY/WAIT) and exit (held positions → SELL), rule-based counted conditions, no numerical scoring.
- Sharp-move warning rule (>5% 1-day or >10% 7-day) overrides enthusiasm: "check the news first."
- No loss-cutting logic in MVP — losing positions shown clearly, no suggestion.
- Positions derived from a trade log (event-sourced), not stored mutably.
- Delayed (15-min) quotes are acceptable; UI always shows data freshness.
- Excluded from MVP: automated trading, broker sync, alerts/notifications, news analysis, backtesting, intraday charts, taxes, accounts, mobile.
- Full details: docs/api-contract.md and docs/plan.md.