import { fmtPrice, fmtPct, fmtVolume, fmtRounded } from "../../lib/format";

function Row({ label, value }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-b border-border py-2 last:border-b-0">
      <dt className="text-[12px] text-ink-muted">{label}</dt>
      <dd className="num m-0 text-[13px] font-semibold whitespace-nowrap">{value}</dd>
    </div>
  );
}

/**
 * @param {{ indicators: import('../../api/types').Indicators }} props
 * Two-column indicator grid matching the reference's `.indicators` layout.
 */
export function IndicatorsPanel({ indicators: ind }) {
  return (
    <div className="grid grid-cols-1 gap-x-8 sm:grid-cols-2">
      <dl className="flex flex-col">
        <Row label="Current price" value={fmtPrice(ind.currentPrice)} />
        <Row label="1-day change" value={fmtPct(ind.change1dPct)} />
        <Row label="7-day change" value={fmtPct(ind.change7dPct)} />
        <Row label="30-day average" value={fmtPrice(ind.thirtyDayAverage)} />
        <Row label="30-day high" value={fmtPrice(ind.thirtyDayHigh)} />
        <Row label="30-day low" value={fmtPrice(ind.thirtyDayLow)} />
      </dl>
      <dl className="flex flex-col">
        <Row label="Distance from 30-day high" value={fmtPct(ind.distanceFromHighPct)} />
        <Row label="Distance from 30-day low" value={fmtPct(ind.distanceFromLowPct)} />
        <Row label="RSI (14-day)" value={fmtRounded(ind.rsi)} />
        <Row label="Today's volume" value={fmtVolume(ind.todaysVolume)} />
        <Row label="Average volume" value={fmtVolume(ind.averageVolume)} />
        <Row label="Volume vs. average" value={fmtPct(ind.volumeVsAveragePct)} />
      </dl>
    </div>
  );
}
