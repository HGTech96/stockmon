import { TrendingUp, TrendingDown, Minus, Clock } from "lucide-react";

const VARIANTS = {
  BUY: { text: "Possible buy", Icon: TrendingUp, classes: "bg-good-bg text-good border-good-border" },
  SELL: { text: "Possible sell", Icon: TrendingDown, classes: "bg-warn-bg text-warn border-warn-border" },
  WAIT: { text: "Wait", Icon: Minus, classes: "bg-neutral-bg text-neutral border-neutral-border" },
  INSUFFICIENT: { text: "Not enough data", Icon: Clock, classes: "bg-surface-sunken text-ink-muted border-border-strong" },
};

/**
 * @param {{ label: "BUY"|"WAIT"|"SELL"|"INSUFFICIENT", size?: "sm"|"lg" }} props
 * Colors are semantic and fixed per CLAUDE.md: BUY=good, SELL=warn (orange,
 * not red), WAIT=neutral gray. "INSUFFICIENT" isn't a suggestion.label value
 * -- pass it when `status === "insufficient_history"` (suggestion is null
 * in that case, so this is a status-driven variant, not part of the
 * Suggestion object).
 */
export function SuggestionBadge({ label, size = "sm" }) {
  const variant = VARIANTS[label];
  const isLg = size === "lg";

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm border font-bold uppercase tracking-wide whitespace-nowrap ${variant.classes} ${
        isLg ? "px-3.5 py-1.5 text-[12.5px]" : "px-2.5 py-1 text-[11px]"
      }`}
    >
      <variant.Icon className={isLg ? "h-[14px] w-[14px]" : "h-[12px] w-[12px]"} strokeWidth={2} />
      {variant.text}
    </span>
  );
}
