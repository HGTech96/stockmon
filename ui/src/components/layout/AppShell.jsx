import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "motion/react";
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
  const location = useLocation();
  useDataRefresh();

  // Crossfade key: collapse /screener and /screener/:ticker to one key so
  // that section (ScreenerSection) never remounts on that internal nav --
  // it holds sort/filter state above both routes (see ScreenerSection's
  // doc comment) that must survive navigating list -> detail -> back.
  const crossfadeKey = location.pathname.startsWith("/screener") ? "screener" : location.pathname;

  return (
    <div className="min-h-screen bg-bg">
      <div className="noise-overlay" aria-hidden="true" />

      <header className="sticky top-0 z-40 flex h-[60px] items-stretch gap-8 border-b border-border bg-bg/95 px-7 backdrop-blur-sm">
        <div className="my-1.5 flex items-center whitespace-nowrap">
          <img src="/full-logo.svg" alt="stockmon" className="h-11 w-auto" />
        </div>
        <NavTabs />
        <div className="flex items-center gap-2.5 whitespace-nowrap">
          <FreshnessBar meta={meta} />
        </div>
      </header>

      <AnimatePresence>
        {meta?.isStale && meta.staleMessage && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="overflow-hidden border-b border-warn-border bg-warn-bg"
          >
            <div className="px-7 py-2.5 text-[13px] font-medium text-warn">{meta.staleMessage}</div>
          </motion.div>
        )}
      </AnimatePresence>

      <main className="mx-auto max-w-[1360px] px-7 pt-7 pb-20">
        <AnimatePresence mode="wait">
          <motion.div
            key={crossfadeKey}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
          >
            <Outlet context={{ setMeta }} />
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
