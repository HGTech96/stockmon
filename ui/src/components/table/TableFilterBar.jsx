import { Search, X } from "lucide-react";

const SUGGESTION_CHIPS = [
  { label: "BUY", text: "Possible buy", activeClasses: "bg-good-bg text-good border-good-border" },
  { label: "WAIT", text: "Wait", activeClasses: "bg-neutral-bg text-neutral border-neutral-border" },
  { label: "SELL", text: "Possible sell", activeClasses: "bg-warn-bg text-warn border-warn-border" },
  { label: "INSUFFICIENT", text: "Not enough data", activeClasses: "bg-surface-sunken text-ink-muted border-border-strong" },
];

const INACTIVE_CHIP_CLASSES = "bg-surface text-ink-muted border-border-strong hover:bg-surface-sunken";

const OWNED_OPTIONS = [
  { value: "all", label: "All" },
  { value: "owned", label: "Owned" },
  { value: "not_owned", label: "Not owned" },
];

/**
 * @param {{
 *   filters: import('../../lib/tableViewState').FilterState,
 *   onSearch: (text: string) => void,
 *   onToggleSuggestion: (label: string) => void,
 *   onOwnedChange: (value: "all"|"owned"|"not_owned") => void,
 *   onReset: () => void,
 *   showOwnedToggle?: boolean,
 *   isFiltered: boolean,
 * }} props
 * Row/suggestion/owned filter controls, sitting inside the table shell
 * directly above the header (same home as sorting -- these act on the
 * visible rows, not the underlying data). Suggestion chips reuse
 * SuggestionBadge's exact text and color classes so "filter to buys" maps
 * to the same green the user already reads in the table; only filled vs.
 * muted changes with active state.
 */
export function TableFilterBar({ filters, onSearch, onToggleSuggestion, onOwnedChange, onReset, showOwnedToggle = false, isFiltered }) {
  return (
    <div className="flex flex-wrap items-center gap-2.5 border-b border-border bg-surface px-4.5 py-3">
      <div className="relative min-w-[180px] flex-1">
        <Search className="pointer-events-none absolute top-1/2 left-2.5 h-3.5 w-3.5 -translate-y-1/2 text-ink-faint" strokeWidth={1.8} />
        <input
          type="text"
          value={filters.search}
          onChange={(e) => onSearch(e.target.value)}
          placeholder="Search ticker or company"
          className="w-full rounded-lg border border-border-strong bg-surface py-1.5 pr-3 pl-8 text-[13px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
        />
      </div>

      <div className="flex flex-wrap items-center gap-1.5">
        {SUGGESTION_CHIPS.map((chip) => {
          const active = filters.suggestions.has(chip.label);
          return (
            <button
              key={chip.label}
              type="button"
              onClick={() => onToggleSuggestion(chip.label)}
              aria-pressed={active}
              className={`rounded-pill border px-2.5 py-1 text-[11.5px] font-bold uppercase tracking-wide whitespace-nowrap ${
                active ? chip.activeClasses : INACTIVE_CHIP_CLASSES
              }`}
            >
              {chip.text}
            </button>
          );
        })}
      </div>

      {showOwnedToggle && (
        <div className="flex overflow-hidden rounded-lg border border-border-strong">
          {OWNED_OPTIONS.map((opt, i) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => onOwnedChange(opt.value)}
              className={`px-3 py-1.5 text-[12.5px] font-semibold whitespace-nowrap ${i > 0 ? "border-l border-border-strong" : ""} ${
                filters.owned === opt.value ? "bg-accent-soft text-accent-ink" : "bg-surface text-ink-muted"
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {isFiltered && (
        <button
          type="button"
          onClick={onReset}
          className="inline-flex items-center gap-1 text-[12.5px] font-semibold text-ink-muted hover:text-ink"
        >
          <X className="h-3 w-3" strokeWidth={2} />
          Clear filters
        </button>
      )}
    </div>
  );
}
