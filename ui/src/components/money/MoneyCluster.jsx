/**
 * @param {{ label: string, live?: boolean, actions?: import('react').ReactNode, children: import('react').ReactNode }} props
 * One labeled group inside MoneyStrip (Cash / Realized / Unrealized) --
 * header row (label, optional live tint, optional right-aligned actions
 * slot for Deposit/Withdraw) above a row of MoneyTiles passed as children.
 *
 * The header row is a fixed `h-9` -- every cluster's header must share this
 * exact height regardless of its content (e.g. Cash's Deposit/Withdraw
 * buttons), otherwise that column's tile row starts lower than its
 * siblings and the bottom edges no longer line up.
 */
export function MoneyCluster({ label, live = false, actions, children }) {
  return (
    <div className="flex flex-col">
      <div
        className={`flex h-9 flex-none items-center justify-between gap-2 border-b border-border px-5 text-[11px] font-bold tracking-wide uppercase ${
          live ? "bg-accent-soft text-accent-ink" : "bg-surface-sunken text-ink-muted"
        }`}
      >
        <span className="inline-flex items-center gap-1.5">
          {live && <span className="h-1.5 w-1.5 rounded-full bg-accent" />}
          {label}
        </span>
        {actions}
      </div>
      <div className="flex flex-1 divide-x divide-border">{children}</div>
    </div>
  );
}
