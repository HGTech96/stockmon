const VARIANTS = {
  buy: { text: "Buy", classes: "bg-good-bg text-good border-good-border" },
  sell: { text: "Sell", classes: "bg-warn-bg text-warn border-warn-border" },
};

/**
 * @param {{ action: "buy"|"sell" }} props
 * Trade-action pill, same shape as SuggestionBadge. Colors are semantic and
 * fixed per CLAUDE.md: buy=good (green), sell=warn (orange, not red).
 */
export function ActionBadge({ action }) {
  const variant = VARIANTS[action];

  return (
    <span
      className={`inline-flex items-center rounded-pill border px-2.5 py-1 text-[11.5px] font-bold uppercase tracking-wide whitespace-nowrap ${variant.classes}`}
    >
      {variant.text}
    </span>
  );
}
