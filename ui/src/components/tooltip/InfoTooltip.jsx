import { Info } from "lucide-react";

/**
 * @param {{ text: string }} props
 * Small inline (i) icon that reveals a short plain-language explanation on
 * hover/focus. CSS-only (group-hover/group-focus-within), no JS state --
 * matches this app's raw-Tailwind styling convention rather than pulling in
 * a Radix tooltip primitive for a couple of call sites.
 */
export function InfoTooltip({ text }) {
  return (
    <span className="group relative inline-flex align-middle">
      <Info
        className="h-3 w-3 flex-none cursor-help text-ink-faint outline-none hover:text-ink-muted"
        strokeWidth={1.8}
        tabIndex={0}
      />
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full left-1/2 z-50 mb-1.5 w-max max-w-[220px] -translate-x-1/2 rounded-lg border border-border-strong bg-ink px-2.5 py-1.5 text-[11.5px] leading-snug text-white opacity-0 shadow-pop transition-opacity group-hover:opacity-100 group-focus-within:opacity-100"
      >
        {text}
      </span>
    </span>
  );
}
