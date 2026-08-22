/**
 * @param {{ label: string, live?: boolean, actions?: import('react').ReactNode, children: import('react').ReactNode }} props
 * One labeled group inside MoneyStrip (Cash / Realized / Unrealized) --
 * header row (label, optional "still moving" live indicator, optional
 * right-aligned actions slot for Deposit/Withdraw) above a row of
 * MoneyTiles passed as children.
 *
 * `h-full flex-col` + the tile row's `flex-1` make the tile row consume
 * all remaining height once MoneyStrip's outer grid stretches this
 * cluster to match its tallest sibling (e.g. Cash's "real money put in"
 * sub-caption makes it taller than Realized/Unrealized) -- flex's default
 * stretch then grows each MoneyTile to fill that height too, so every
 * cluster's bottom edge lands on the same line and a tile's tint (its own
 * background) covers the whole cell instead of just its text's natural
 * height.
 */
export function MoneyCluster({ label, live = false, actions, children }) {
  return (
    <div className="flex h-full flex-col bg-surface">
      <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-2.5">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold tracking-wide text-ink-muted uppercase">{label}</span>
          {live && (
            <span className="flex items-center gap-1.5 text-[11px] text-ink-faint">
              <span className="h-1.5 w-1.5 animate-pulse rounded-pill bg-accent" aria-hidden="true" />
              moves with the market
            </span>
          )}
        </div>
        {actions}
      </div>
      <div className="flex flex-1 gap-px bg-border">{children}</div>
    </div>
  );
}
