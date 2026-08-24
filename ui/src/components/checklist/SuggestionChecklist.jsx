import { Check, X } from "lucide-react";
import { InfoTooltip } from "../tooltip/InfoTooltip";

/**
 * Short plain-language explanations for checklist items whose wording
 * alone can be jargon-y to a non-finance reader. Keyed by the backend's
 * stable machine `id` (docs/api-contract.md) -- purely educational glossary
 * text, not a re-derivation of the suggestion logic, so it doesn't conflict
 * with "the backend is the single source of wording" for the checklist text
 * itself.
 */
const ITEM_EXPLANATIONS = {
  rsi_low: "RSI is a 0–100 momentum score for how fast the price has moved recently — lower usually means less overbought.",
  rsi_high: "RSI is a 0–100 momentum score for how fast the price has moved recently — higher usually means more overbought.",
  volume_above_avg: "Volume is how many shares changed hands today. Higher-than-average volume can signal stronger interest in the move.",
};

/**
 * @param {{ suggestion: import('../../api/types').Suggestion }} props
 * The "Why · N of M conditions met" box: pass/fail list (icon + item.text,
 * both driven by the backend so wording and logic can never diverge) and
 * `note` when present. Per CLAUDE.md a badge is never rendered without this
 * nearby -- callers compose the two together; this component never renders
 * a badge itself.
 */
export function SuggestionChecklist({ suggestion }) {
  const { metCount, totalCount, checklist, note } = suggestion;

  return (
    <div>
      <div className="mb-2.5 text-xs font-bold tracking-wide text-ink-muted uppercase">
        Why &middot; {metCount} of {totalCount} conditions met
      </div>
      <ul className="flex flex-col gap-2.5">
        {checklist.map((item) => (
          <li key={item.id} className={`flex items-start gap-2.5 text-[13.5px] leading-snug ${item.passed ? "" : "text-ink-muted"}`}>
            <span
              className={`mt-0.5 flex h-[18px] w-[18px] flex-none items-center justify-center rounded-full ${
                item.passed ? "bg-good-bg text-good" : "bg-surface-sunken text-ink-faint"
              }`}
            >
              {item.passed ? <Check className="h-[11px] w-[11px]" strokeWidth={2.5} /> : <X className="h-[11px] w-[11px]" strokeWidth={2.5} />}
            </span>
            <span>
              {item.text}
              {ITEM_EXPLANATIONS[item.id] && (
                <>
                  {" "}
                  <InfoTooltip text={ITEM_EXPLANATIONS[item.id]} />
                </>
              )}
            </span>
          </li>
        ))}
      </ul>
      {note && <div className="mt-2.5 text-[12.5px] text-ink-muted">{note}</div>}
    </div>
  );
}
