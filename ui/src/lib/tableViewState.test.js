import { describe, expect, it } from "vitest";
import { applyTableViewState, cycleSort } from "./tableViewState";

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
