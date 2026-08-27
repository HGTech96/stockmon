import { useState } from "react";
import { Outlet, useOutletContext } from "react-router-dom";
import { EMPTY_FILTER_STATE } from "../../lib/tableViewState";

/**
 * Pathless layout route wrapping /screener and /screener/:ticker. Holds the
 * screener table's sort/filter state above both routes so it survives
 * navigating from the table to a row's detail page and back -- the sibling
 * routes would otherwise fully unmount ScreenerPage and lose it. Leaving
 * the screener section entirely (a nav tab, or a reload) unmounts this too,
 * so the "reset to server default" rule (CLAUDE.md) still holds there --
 * this only changes what counts as "leaving."
 */
export function ScreenerSection() {
  const parentContext = useOutletContext();
  const [sort, setSort] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTER_STATE);

  return <Outlet context={{ ...parentContext, screenerViewState: { sort, setSort, filters, setFilters } }} />;
}
