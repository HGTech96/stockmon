import {
  ResponsiveContainer,
  ComposedChart,
  CartesianGrid,
  XAxis,
  YAxis,
  Line,
  Bar,
  Cell,
  ReferenceLine,
  Tooltip,
} from "recharts";
import { fmtPrice, fmtVolume, fmtDateShort, fmtDateLong } from "../../lib/format";

const CHART_HEIGHT = 260;
/** Volume bars are scaled onto a y-axis padded to 4x the max value, so
 * they only occupy the bottom band of the chart -- matching the reference's
 * separate stacked price/volume panes without needing two synced charts. */
const VOLUME_DOMAIN_MULTIPLIER = 4;

function priceDomain(days, thirtyDayAverage, userAvgPurchasePrice) {
  const closes = days.map((d) => d.close);
  let min = Math.min(...closes, thirtyDayAverage, userAvgPurchasePrice ?? Infinity);
  let max = Math.max(...closes, thirtyDayAverage, userAvgPurchasePrice ?? -Infinity);
  const range = max - min || 1;
  return [min - range * 0.1, max + range * 0.1];
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const day = payload[0].payload;
  return (
    <div className="rounded-lg bg-ink px-2.5 py-2 text-xs text-white shadow-pop">
      <div className="mb-0.5 font-semibold">{fmtDateLong(day.date)}</div>
      <div className="flex justify-between gap-3">
        <span className="text-white/60">Close</span>
        <span>{fmtPrice(day.close)}</span>
      </div>
      <div className="flex justify-between gap-3">
        <span className="text-white/60">Volume</span>
        <span>{fmtVolume(day.volume)}</span>
      </div>
    </div>
  );
}

function todaysDot({ cx, cy, index, days, color }) {
  if (index !== days.length - 1) return null;
  return <circle cx={cx} cy={cy} r={4} fill={color} stroke="var(--color-surface)" strokeWidth={1.5} />;
}

/**
 * @param {{ chart: import('../../api/types').ChartData, change7dPct: number }} props
 * 30-day price + volume, one shared time axis per contract (`chart.days`).
 * `chart.userAvgPurchasePrice` is null when the stock isn't owned, so the
 * dashed avg-cost line and its legend entry simply don't render -- no
 * ownership flag threaded in separately. The price line/dots pick up the
 * app's existing good/bad tokens (same green/red used for P/L elsewhere)
 * based on the 7-day trend direction -- negative is red, non-negative green.
 */
export function PriceVolumeChart({ chart, change7dPct }) {
  const { days, thirtyDayAverage, userAvgPurchasePrice } = chart;
  const maxVolume = Math.max(...days.map((d) => d.volume));
  const trendColor = change7dPct < 0 ? "var(--color-bad)" : "var(--color-good)";

  return (
    <div>
      <div className="mb-1 flex gap-4 text-xs text-ink-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-0.5 w-3.5 flex-none" style={{ backgroundColor: trendColor }} />
          Price
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-3.5 flex-none border-t border-dashed border-ink-faint" />
          30-day average
        </span>
        {userAvgPurchasePrice != null && (
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 flex-none border-t border-dashed border-accent" />
            Your average cost
          </span>
        )}
      </div>

      <ResponsiveContainer width="100%" height={CHART_HEIGHT}>
        <ComposedChart data={days} margin={{ top: 8, right: 4, bottom: 0, left: 4 }}>
          <CartesianGrid vertical={false} stroke="var(--color-border)" />
          <XAxis dataKey="date" hide />
          <YAxis
            yAxisId="price"
            hide
            domain={priceDomain(days, thirtyDayAverage, userAvgPurchasePrice)}
          />
          <YAxis yAxisId="volume" hide domain={[0, maxVolume * VOLUME_DOMAIN_MULTIPLIER]} />

          <Bar yAxisId="volume" dataKey="volume" radius={[1, 1, 0, 0]} maxBarSize={14}>
            {days.map((day, i) => (
              <Cell key={day.date} fill={i === days.length - 1 ? "var(--color-accent)" : "var(--color-border-strong)"} />
            ))}
          </Bar>

          <ReferenceLine
            yAxisId="price"
            y={thirtyDayAverage}
            stroke="var(--color-ink-faint)"
            strokeDasharray="3 3"
          />
          {userAvgPurchasePrice != null && (
            <ReferenceLine
              yAxisId="price"
              y={userAvgPurchasePrice}
              stroke="var(--color-accent)"
              strokeDasharray="4 3"
              label={{
                value: `Your avg ${fmtPrice(userAvgPurchasePrice)}`,
                position: "insideTopRight",
                fill: "var(--color-accent)",
                fontSize: 10.5,
                fontWeight: 600,
              }}
            />
          )}

          <Line
            yAxisId="price"
            type="monotone"
            dataKey="close"
            stroke={trendColor}
            strokeWidth={3}
            dot={(props) => todaysDot({ ...props, days, color: trendColor })}
            activeDot={{ r: 4.5, fill: trendColor, stroke: "var(--color-surface)", strokeWidth: 1.5 }}
            isAnimationActive={false}
          />

          <Tooltip content={<ChartTooltip />} cursor={{ stroke: "var(--color-ink-faint)", strokeDasharray: "2 3" }} />
        </ComposedChart>
      </ResponsiveContainer>

      <div className="mt-1.5 flex justify-between text-[11px] text-ink-faint">
        <span>{fmtDateShort(days[0].date)}</span>
        <span>{fmtDateShort(days[Math.floor(days.length / 2)].date)}</span>
        <span>{fmtDateShort(days[days.length - 1].date)}</span>
      </div>
    </div>
  );
}
