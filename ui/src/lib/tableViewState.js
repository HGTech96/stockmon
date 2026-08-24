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
