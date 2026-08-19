import { useState } from "react";
import { Outlet } from "react-router-dom";
import { NavTabs } from "./NavTabs";
import { FreshnessBar } from "./FreshnessBar";
import { useDataRefresh } from "../../hooks/useDataRefresh";

/**
 * Top nav + freshness indicator + (when stale) the full-width stale
 * banner, wrapping every page via <Outlet/>. The active page reports its
 * own query's `meta` block up through the outlet context's `setMeta` --
 * each GET response carries its own freshness data per the contract, so
 * the shell has no fetch of its own.
 */
export function AppShell() {
  const [meta, setMeta] = useState(undefined);
  useDataRefresh();

  return (
    <div className="min-h-screen bg-bg">
      <header className="sticky top-0 z-40 flex h-[60px] items-stretch gap-8 border-b border-border-strong bg-bg px-7">
        <div className="flex items-center text-[15px] font-bold tracking-tight whitespace-nowrap">
          Stock Helper
        </div>
        <NavTabs />
        <div className="flex items-center gap-2.5 whitespace-nowrap">
          <FreshnessBar meta={meta} />
        </div>
      </header>

      {meta?.isStale && meta.staleMessage && (
        <div className="border-b border-warn-border bg-warn-bg px-7 py-2.5 text-[13px] font-medium text-warn">
          {meta.staleMessage}
        </div>
      )}

      <main className="mx-auto max-w-[1360px] px-7 pt-7 pb-20">
        <Outlet context={{ setMeta }} />
      </main>
    </div>
  );
}
