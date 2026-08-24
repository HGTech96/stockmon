import { useState } from "react";
import { applyTableViewState, cycleSort } from "../lib/tableViewState";

/**
 * Table-level view-state: holds the user's column-sort choice and applies
 * it to already-fetched rows. No persistence -- state lives only in this
 * component instance, so a reload always lands back on the server default.
 * @param {Array} rows
 * @param {import('../lib/tableViewState').SortColumn[]} columns
 */
export function useTableViewState(rows, columns) {
  const [sort, setSort] = useState(null);

  function toggleSort(key) {
    setSort((current) => cycleSort(current, key));
  }

  return {
    rows: applyTableViewState(rows, columns, { sort }),
    sort,
    toggleSort,
  };
}
