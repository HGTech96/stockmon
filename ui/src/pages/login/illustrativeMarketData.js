/**
 * Static, clearly-labeled-as-illustrative numbers for the login page's
 * hero panel (see LiveMarketPanel's footer copy) -- the login screen has
 * no session yet, so it can't show the visitor's real watchlist. Not
 * fetched from the API and never presented as real data.
 */
export const ILLUSTRATIVE_STOCKS = [
  { ticker: "NVDA", currentPrice: 187.42, change1dPct: 3.18 },
  { ticker: "TSLA", currentPrice: 268.91, change1dPct: -2.44 },
  { ticker: "AMD", currentPrice: 154.06, change1dPct: 1.02 },
  { ticker: "PLTR", currentPrice: 41.73, change1dPct: 5.61 },
];

function buildIllustrativeSparkline(start, end, points = 30) {
  const values = [];
  for (let i = 0; i < points; i++) {
    const t = i / (points - 1);
    const base = start + (end - start) * t;
    const noise = (Math.sin(i * 1.7) + Math.sin(i * 0.6)) * (Math.abs(end - start) * 0.06);
    values.push(Math.max(base + noise, 0.5));
  }
  values[values.length - 1] = end;
  return values;
}

export const ILLUSTRATIVE_SPARKLINE = buildIllustrativeSparkline(162.1, 187.42);
