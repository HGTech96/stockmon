/**
 * Generic row-ordering engine shared by every sortable table (StockTable,
 * PositionsTable). Reorders already-fetched rows only -- never mutates,
 * never fetches, never computes a value the API didn't send.
 *
 * Phase 13 filtering plugs into the same `viewState` object (adding a
 * `filters` key alongside `sort`) without changing this function's
 * contract: rows in, rows out.
 */

/**
 * @typedef {Object} SortColumn
 * @property {string} key
 * @property {(row: any) => (string|number|null)} accessor
 * @property {"string"|"number"} sortType
 */

/**
 * @typedef {Object} SortState
 * @property {string} key
 * @property {"asc"|"desc"} direction
 */

function compareBySortType(a, b, sortType) {
  if (sortType === "number") return a - b;
  return String(a).localeCompare(String(b));
}

/**
 * Null-ness is decided before direction is applied, so nulls land last
 * regardless of asc/desc -- only the ordering of non-null values flips.
 */
function compareNullable(a, b, direction, sortType) {
  const aNull = a == null;
  const bNull = b == null;
  if (aNull && bNull) return 0;
  if (aNull) return 1;
  if (bNull) return -1;

  const result = compareBySortType(a, b, sortType);
  return direction === "desc" ? -result : result;
}

/**
 * @param {Array} rows
 * @param {SortColumn[]} columns
 * @param {{ sort: SortState|null }} viewState
 * @returns {Array} new array in view order; `rows` itself is never mutated.
 * When `viewState.sort` is null (the server-default state), returns `rows`
 * unchanged -- so `Array.prototype.sort`'s stability never even comes into
 * play there.
 */
export function applyTableViewState(rows, columns, viewState) {
  const { sort } = viewState;
  if (!sort) return rows;

  const column = columns.find((c) => c.key === sort.key);
  if (!column) return rows;

  return [...rows].sort((rowA, rowB) => compareNullable(column.accessor(rowA), column.accessor(rowB), sort.direction, column.sortType));
}

/**
 * @param {SortState|null} currentSort
 * @param {string} key
 * @returns {SortState|null} the next state in the asc -> desc -> server-default cycle.
 * Clicking a different column always restarts at asc.
 */
export function cycleSort(currentSort, key) {
  if (!currentSort || currentSort.key !== key) return { key, direction: "asc" };
  if (currentSort.direction === "asc") return { key, direction: "desc" };
  return null;
}

/**
 * @typedef {Object} FilterConfig
 * @property {(row: any) => string} searchText - pre-joined lowercased ticker + companyName
 * @property {(row: any) => ("BUY"|"WAIT"|"SELL"|"INSUFFICIENT")} suggestion
 * @property {(row: any) => boolean} [owned] - omitted on tables with no owned toggle (Portfolio)
 */

/**
 * @typedef {Object} FilterState
 * @property {string} search
 * @property {Set<"BUY"|"WAIT"|"SELL"|"INSUFFICIENT">} suggestions - empty set = no filter
 * @property {"all"|"owned"|"not_owned"} owned - ignored when FilterConfig.owned is absent
 */

/** @type {FilterState} */
export const EMPTY_FILTER_STATE = { search: "", suggestions: new Set(), owned: "all" };

/**
 * @param {FilterState} filters
 * @returns {boolean} true if any filter would narrow the row set -- drives
 * reset-button visibility and the empty-result vs. genuinely-empty distinction.
 */
export function isFilterActive(filters) {
  return filters.search.trim() !== "" || filters.suggestions.size > 0 || filters.owned !== "all";
}

/**
 * @param {Array} rows
 * @param {FilterConfig} config
 * @param {FilterState} filters
 * @returns {Array} new array of rows matching every active filter (AND'd
 * together); never mutates `rows`. Runs before `applyTableViewState` --
 * filtering narrows, sorting orders what remains.
 */
export function filterRows(rows, config, filters) {
  const search = filters.search.trim().toLowerCase();

  return rows.filter((row) => {
    if (search && !config.searchText(row).toLowerCase().includes(search)) return false;
    if (filters.suggestions.size > 0 && !filters.suggestions.has(config.suggestion(row))) return false;
    if (config.owned && filters.owned !== "all") {
      const owned = config.owned(row);
      if (filters.owned === "owned" && !owned) return false;
      if (filters.owned === "not_owned" && owned) return false;
    }
    return true;
  });
}
