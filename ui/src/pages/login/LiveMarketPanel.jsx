import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { fmtPrice } from "../../lib/format";
import { Trend } from "../../components/trend/Trend";
import { useTweenedNumber } from "../../hooks/useTweenedNumber";
import { MiniSparkline } from "./MiniSparkline";
import { ILLUSTRATIVE_SPARKLINE, ILLUSTRATIVE_STOCKS } from "./illustrativeMarketData";

function tickRow(stock) {
  const drift = (Math.random() - 0.5) * stock.currentPrice * 0.01;
  const currentPrice = Math.max(stock.currentPrice + drift, 0.5);
  const change1dPct = stock.change1dPct + (drift / stock.currentPrice) * 100;
  return { ...stock, currentPrice, change1dPct };
}

/**
 * The login screen's hero: a live-ticking miniature of the real watchlist,
 * so the product's core loop (price moves in, a clear signal comes out) is
 * visible before you're even signed in. Uses static illustrative numbers
 * (see illustrativeMarketData.js) -- there's no session yet to fetch a
 * real watchlist with.
 */
export function LiveMarketPanel() {
  const [rows, setRows] = useState(ILLUSTRATIVE_STOCKS);
  const [justUpdated, setJustUpdated] = useState(null);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const interval = setInterval(() => {
      setRows((prev) => {
        const target = prev[Math.floor(Math.random() * prev.length)];
        setJustUpdated(target.ticker);
        window.setTimeout(() => setJustUpdated((cur) => (cur === target.ticker ? null : cur)), 1100);
        return prev.map((s) => (s.ticker === target.ticker ? tickRow(s) : s));
      });
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="rounded-DEFAULT border border-white/10 bg-white/[0.04] p-5 backdrop-blur-sm">
      <div className="mb-4 flex items-center justify-between">
        <span className="text-[11.5px] font-semibold tracking-[0.08em] text-white/50 uppercase">Watchlist · live</span>
        <span className="flex items-center gap-1.5 text-[11px] font-medium text-white/40">
          <span className="relative flex h-[6px] w-[6px]">
            {!reduceMotion && (
              <motion.span
                className="absolute inline-flex h-full w-full rounded-full bg-good"
                animate={{ scale: [1, 2.2], opacity: [0.6, 0] }}
                transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
              />
            )}
            <span className="relative inline-flex h-[6px] w-[6px] rounded-full bg-good" />
          </span>
          streaming
        </span>
      </div>

      <MiniSparkline values={ILLUSTRATIVE_SPARKLINE} height={92} />

      <div className="mt-4 flex flex-col gap-0.5">
        {rows.map((stock) => (
          <WatchRow key={stock.ticker} stock={stock} flash={justUpdated === stock.ticker} />
        ))}
      </div>
    </div>
  );
}

function WatchRow({ stock, flash }) {
  const price = useTweenedNumber(stock.currentPrice);
  const change1dPct = useTweenedNumber(stock.change1dPct);
  const flashColor = stock.change1dPct >= 0 ? "rgba(21, 128, 61, 0.24)" : "rgba(200, 16, 46, 0.24)";

  return (
    <div
      style={{ backgroundColor: flash ? flashColor : "rgba(255,255,255,0)", transition: "background-color 1.1s ease-out" }}
      className="flex items-center justify-between rounded-sm px-2 py-1.5"
    >
      <span className="text-[12.5px] font-bold text-white/90">{stock.ticker}</span>
      <div className="flex items-center gap-3">
        <span className="num text-[12.5px] text-white/70">{fmtPrice(price)}</span>
        <Trend pct={change1dPct} />
      </div>
    </div>
  );
}
