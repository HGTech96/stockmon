import { useEffect, useRef, useState } from "react";

const FLASH_DURATION_MS = 1100;

/**
 * Tracks which tickers' currentPrice changed since the last render of
 * `stocks`, for the row price-flash effect. Purely presentational (drives
 * a transient background-color transition, nothing rendered/derived) --
 * clears itself after the flash duration.
 */
export function useRecentlyUpdated(stocks) {
  const previousPrices = useRef(new Map());
  const [recentlyUpdated, setRecentlyUpdated] = useState(new Set());

  useEffect(() => {
    if (!stocks) return;
    const prev = previousPrices.current;
    const changed = new Set();
    for (const stock of stocks) {
      const prevPrice = prev.get(stock.ticker);
      if (prevPrice != null && prevPrice !== stock.currentPrice) {
        changed.add(stock.ticker);
      }
      prev.set(stock.ticker, stock.currentPrice);
    }
    if (changed.size === 0) return undefined;
    setRecentlyUpdated(changed);
    const timer = setTimeout(() => setRecentlyUpdated(new Set()), FLASH_DURATION_MS);
    return () => clearTimeout(timer);
  }, [stocks]);

  return recentlyUpdated;
}
