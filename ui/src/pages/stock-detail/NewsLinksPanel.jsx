import { ExternalLink } from "lucide-react";

function NewsLink({ href, children }) {
  return (
    <a
      className="flex items-center justify-between rounded-lg border border-border px-3 py-2.5 text-[13px] font-semibold text-ink no-underline hover:border-border-strong hover:bg-surface-sunken"
      href={href}
      target="_blank"
      rel="noopener"
    >
      {children}
      <ExternalLink className="h-3.5 w-3.5 text-ink-faint" strokeWidth={1.4} />
    </a>
  );
}

/**
 * @param {{ newsLinks: import('../../api/types').NewsLinks }} props
 * Yahoo/Google links always render; `investorRelations` only when the
 * backend actually sent one -- never a fabricated search-link fallback.
 */
export function NewsLinksPanel({ newsLinks }) {
  return (
    <div>
      <div className="mb-3.5 flex flex-col gap-2">
        <NewsLink href={newsLinks.yahooFinance}>Yahoo Finance</NewsLink>
        <NewsLink href={newsLinks.googleFinance}>Google Finance</NewsLink>
        {newsLinks.investorRelations && <NewsLink href={newsLinks.investorRelations}>Investor relations</NewsLink>}
      </div>
      <div className="rounded-lg bg-surface-sunken px-3 py-2.5 text-xs leading-relaxed text-ink-muted">
        Unusual price moves can be caused by company news that these numbers cannot explain.
      </div>
    </div>
  );
}
