import { describe, expect, it } from "vitest";
import { applyTableViewState, cycleSort, EMPTY_FILTER_STATE, filterRows, isFilterActive } from "./tableViewState";

const NUMERIC_COLUMNS = [{ key: "price", accessor: (r) => r.price, sortType: "number" }];
const STRING_COLUMNS = [{ key: "label", accessor: (r) => r.label, sortType: "string" }];

describe("applyTableViewState", () => {
  it("sorts a numeric column ascending", () => {
    const rows = [{ price: 30 }, { price: 10 }, { price: 20 }];
    const result = applyTableViewState(rows, NUMERIC_COLUMNS, { sort: { key: "price", direction: "asc" } });
    expect(result.map((r) => r.price)).toEqual([10, 20, 30]);
  });

  it("sorts a numeric column descending", () => {
    const rows = [{ price: 30 }, { price: 10 }, { price: 20 }];
    const result = applyTableViewState(rows, NUMERIC_COLUMNS, { sort: { key: "price", direction: "desc" } });
    expect(result.map((r) => r.price)).toEqual([30, 20, 10]);
  });

  it("returns rows in server order when sort is null", () => {
    const rows = [{ price: 30 }, { price: 10 }, { price: 20 }];
    const result = applyTableViewState(rows, NUMERIC_COLUMNS, { sort: null });
    expect(result.map((r) => r.price)).toEqual([30, 10, 20]);
    expect(result).toBe(rows);
  });

  it("does not mutate the input array", () => {
    const rows = [{ price: 30 }, { price: 10 }];
    applyTableViewState(rows, NUMERIC_COLUMNS, { sort: { key: "price", direction: "asc" } });
    expect(rows.map((r) => r.price)).toEqual([30, 10]);
  });

  it("sorts numeric nulls to the bottom ascending", () => {
    const rows = [{ price: 10 }, { price: null }, { price: 5 }];
    const result = applyTableViewState(rows, NUMERIC_COLUMNS, { sort: { key: "price", direction: "asc" } });
    expect(result.map((r) => r.price)).toEqual([5, 10, null]);
  });

  it("sorts numeric nulls to the bottom descending", () => {
    const rows = [{ price: 10 }, { price: null }, { price: 5 }];
    const result = applyTableViewState(rows, NUMERIC_COLUMNS, { sort: { key: "price", direction: "desc" } });
    expect(result.map((r) => r.price)).toEqual([10, 5, null]);
  });

  it("sorts string nulls to the bottom in both directions", () => {
    const rows = [{ label: "WAIT" }, { label: null }, { label: "BUY" }];
    const asc = applyTableViewState(rows, STRING_COLUMNS, { sort: { key: "label", direction: "asc" } });
    expect(asc.map((r) => r.label)).toEqual(["BUY", "WAIT", null]);

    const desc = applyTableViewState(rows, STRING_COLUMNS, { sort: { key: "label", direction: "desc" } });
    expect(desc.map((r) => r.label)).toEqual(["WAIT", "BUY", null]);
  });
});

describe("cycleSort", () => {
  it("starts a fresh column at asc", () => {
    expect(cycleSort(null, "price")).toEqual({ key: "price", direction: "asc" });
  });

  it("advances the same column from asc to desc", () => {
    expect(cycleSort({ key: "price", direction: "asc" }, "price")).toEqual({ key: "price", direction: "desc" });
  });

  it("returns to server default (null) on the third click", () => {
    expect(cycleSort({ key: "price", direction: "desc" }, "price")).toBeNull();
  });

  it("restarts at asc when switching to a different column mid-cycle", () => {
    expect(cycleSort({ key: "price", direction: "desc" }, "ticker")).toEqual({ key: "ticker", direction: "asc" });
  });
});

const STOCKS = [
  { ticker: "AAPL", companyName: "Apple Inc.", status: "ok", suggestion: "BUY", position: { profitLoss: 10 } },
  { ticker: "MSFT", companyName: "Microsoft Corp.", status: "ok", suggestion: "WAIT", position: null },
  { ticker: "TSLA", companyName: "Tesla Inc.", status: "ok", suggestion: "SELL", position: { profitLoss: -5 } },
  { ticker: "NEWCO", companyName: "New Company", status: "insufficient_history", suggestion: null, position: null },
];

const STOCK_FILTER_CONFIG = {
  searchText: (s) => `${s.ticker} ${s.companyName}`,
  suggestion: (s) => (s.status === "insufficient_history" ? "INSUFFICIENT" : s.suggestion),
  owned: (s) => s.position != null,
};

describe("filterRows", () => {
  it("narrows by ticker search, case-insensitive substring", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, search: "aap" });
    expect(result.map((s) => s.ticker)).toEqual(["AAPL"]);
  });

  it("narrows by company name search, case-insensitive substring", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, search: "microsoft" });
    expect(result.map((s) => s.ticker)).toEqual(["MSFT"]);
  });

  it("filters by a single active suggestion", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, suggestions: new Set(["BUY"]) });
    expect(result.map((s) => s.ticker)).toEqual(["AAPL"]);
  });

  it("filters by multiple active suggestions (OR within the set)", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, suggestions: new Set(["BUY", "SELL"]) });
    expect(result.map((s) => s.ticker)).toEqual(["AAPL", "TSLA"]);
  });

  it("treats insufficient-history as its own filterable state, not a suggestion", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, suggestions: new Set(["INSUFFICIENT"]) });
    expect(result.map((s) => s.ticker)).toEqual(["NEWCO"]);
  });

  it("filters to owned rows only", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, owned: "owned" });
    expect(result.map((s) => s.ticker)).toEqual(["AAPL", "TSLA"]);
  });

  it("filters to not-owned rows only", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, owned: "not_owned" });
    expect(result.map((s) => s.ticker)).toEqual(["MSFT", "NEWCO"]);
  });

  it("ignores the owned filter when the config has no owned accessor (Portfolio)", () => {
    const { owned: _owned, ...configWithoutOwned } = STOCK_FILTER_CONFIG;
    const result = filterRows(STOCKS, configWithoutOwned, { ...EMPTY_FILTER_STATE, owned: "owned" });
    expect(result).toHaveLength(STOCKS.length);
  });

  it("ANDs search, suggestion, and owned filters together", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, {
      search: "a",
      suggestions: new Set(["BUY", "SELL"]),
      owned: "owned",
    });
    expect(result.map((s) => s.ticker)).toEqual(["AAPL", "TSLA"]);
  });

  it("returns an empty array when nothing matches", () => {
    const result = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, search: "nonexistent" });
    expect(result).toEqual([]);
  });

  it("does not mutate the input array", () => {
    filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, search: "aapl" });
    expect(STOCKS).toHaveLength(4);
  });
});

describe("filterRows + applyTableViewState combined", () => {
  it("sorts only the rows that survive filtering", () => {
    const priceColumns = [{ key: "profitLoss", accessor: (s) => s.position?.profitLoss ?? null, sortType: "number" }];
    const filtered = filterRows(STOCKS, STOCK_FILTER_CONFIG, { ...EMPTY_FILTER_STATE, owned: "owned" });
    const sorted = applyTableViewState(filtered, priceColumns, { sort: { key: "profitLoss", direction: "asc" } });
    expect(sorted.map((s) => s.ticker)).toEqual(["TSLA", "AAPL"]);
  });
});

describe("isFilterActive", () => {
  it("is false for the empty filter state", () => {
    expect(isFilterActive(EMPTY_FILTER_STATE)).toBe(false);
  });

  it("is true when search text is set", () => {
    expect(isFilterActive({ ...EMPTY_FILTER_STATE, search: "aapl" })).toBe(true);
  });

  it("is true when a suggestion is active", () => {
    expect(isFilterActive({ ...EMPTY_FILTER_STATE, suggestions: new Set(["BUY"]) })).toBe(true);
  });

  it("is true when owned is not 'all'", () => {
    expect(isFilterActive({ ...EMPTY_FILTER_STATE, owned: "owned" })).toBe(true);
  });

  it("resets to false after clearing back to the empty state", () => {
    const dirty = { search: "x", suggestions: new Set(["BUY"]), owned: "owned" };
    expect(isFilterActive(dirty)).toBe(true);
    expect(isFilterActive(EMPTY_FILTER_STATE)).toBe(false);
  });
});
