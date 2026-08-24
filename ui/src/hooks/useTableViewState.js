import { useState } from "react";
import { applyTableViewState, cycleSort, EMPTY_FILTER_STATE, filterRows, isFilterActive } from "../lib/tableViewState";

/**
 * Table-level view-state: holds the user's column-sort choice and filter
 * selections, and applies both to already-fetched rows (filter first, then
 * sort -- filtering narrows, sorting orders what remains). No persistence --
 * state lives only in this component instance, so a reload always lands
 * back on the server default with no filters.
 * @param {Array} rows
 * @param {import('../lib/tableViewState').SortColumn[]} columns
 * @param {import('../lib/tableViewState').FilterConfig} filterConfig
 */
export function useTableViewState(rows, columns, filterConfig) {
  const [sort, setSort] = useState(null);
  const [filters, setFilters] = useState(EMPTY_FILTER_STATE);

  function toggleSort(key) {
    setSort((current) => cycleSort(current, key));
  }

  function setSearch(text) {
    setFilters((current) => ({ ...current, search: text }));
  }

  function toggleSuggestion(label) {
    setFilters((current) => {
      const suggestions = new Set(current.suggestions);
      if (suggestions.has(label)) suggestions.delete(label);
      else suggestions.add(label);
      return { ...current, suggestions };
    });
  }

  function setOwned(value) {
    setFilters((current) => ({ ...current, owned: value }));
  }

  function resetFilters() {
    setFilters(EMPTY_FILTER_STATE);
  }

  const filtered = filterRows(rows, filterConfig, filters);

  return {
    rows: applyTableViewState(filtered, columns, { sort }),
    sort,
    toggleSort,
    filters,
    setSearch,
    toggleSuggestion,
    setOwned,
    resetFilters,
    isFiltered: isFilterActive(filters),
  };
}
