import "@testing-library/jest-dom/vitest";
import { useState } from "react";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_FILTER_STATE } from "../../lib/tableViewState";
import { ScreenerTable } from "./ScreenerTable";

const navigateMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => navigateMock };
});

const RESULTS = [
  {
    ticker: "PLTR",
    companyName: "Palantir Technologies Inc.",
    currentPrice: 27.85,
    change1dPct: 1.52,
    suggestion: "BUY",
    metCount: 3,
    totalCount: 4,
    rsi: 38.0,
    priceVs30dAvgPct: -4.1,
    sharpMove: false,
    status: "ok",
  },
  {
    ticker: "KO",
    companyName: "The Coca-Cola Company",
    currentPrice: 61.2,
    change1dPct: -0.3,
    suggestion: "WAIT",
    metCount: 1,
    totalCount: 4,
    rsi: 55.0,
    priceVs30dAvgPct: 1.8,
    sharpMove: false,
    status: "ok",
  },
  {
    ticker: "ZZZZ",
    companyName: "Recent Listing Inc.",
    currentPrice: 5.1,
    change1dPct: 0.9,
    suggestion: null,
    metCount: null,
    totalCount: null,
    rsi: null,
    priceVs30dAvgPct: null,
    sharpMove: null,
    status: "insufficient_history",
  },
];

function renderTable(results = RESULTS) {
  return render(
    <MemoryRouter>
      <ScreenerTable results={results} />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  navigateMock.mockClear();
});

afterEach(() => {
  cleanup();
});

describe("ScreenerTable", () => {
  it("renders one row per result", () => {
    renderTable();
    const table = within(screen.getByRole("table"));
    expect(table.getByText("PLTR")).toBeInTheDocument();
    expect(table.getByText("KO")).toBeInTheDocument();
    expect(table.getByText("ZZZZ")).toBeInTheDocument();
    expect(table.getByText("Not enough data")).toBeInTheDocument();
  });

  it("sorts by a column ascending then descending then back to server order on the third click", () => {
    renderTable();
    const priceHeader = screen.getByText("Price");

    fireEvent.click(priceHeader);
    let tickerCells = screen.getAllByRole("row").slice(1).map((r) => r.querySelector("td").textContent);
    expect(tickerCells[0]).toContain("ZZZZ"); // lowest price (5.10) first, asc

    fireEvent.click(priceHeader);
    tickerCells = screen.getAllByRole("row").slice(1).map((r) => r.querySelector("td").textContent);
    expect(tickerCells[0]).toContain("KO"); // highest price (61.20) first, desc

    fireEvent.click(priceHeader);
    tickerCells = screen.getAllByRole("row").slice(1).map((r) => r.querySelector("td").textContent);
    expect(tickerCells[0]).toContain("PLTR"); // back to server/input order
  });

  it("filters rows by search text via the shared view-state layer", () => {
    renderTable();
    const search = screen.getByPlaceholderText("Search ticker or company");
    fireEvent.change(search, { target: { value: "coca" } });

    expect(screen.getByText("KO")).toBeInTheDocument();
    expect(screen.queryByText("PLTR")).not.toBeInTheDocument();
    expect(screen.queryByText("ZZZZ")).not.toBeInTheDocument();
  });

  it("filters rows by suggestion chip", () => {
    renderTable();
    fireEvent.click(screen.getByRole("button", { name: "Possible buy" }));

    const table = within(screen.getByRole("table"));
    expect(table.getByText("PLTR")).toBeInTheDocument();
    expect(table.queryByText("KO")).not.toBeInTheDocument();
  });

  it("shows the filtered-empty state distinct from a genuinely empty table, and reset restores rows", () => {
    renderTable();
    const search = screen.getByPlaceholderText("Search ticker or company");
    fireEvent.change(search, { target: { value: "nonexistent-ticker" } });

    expect(screen.getByText("No stocks match your filters")).toBeInTheDocument();
    expect(within(screen.getByRole("table")).queryByText("PLTR")).not.toBeInTheDocument();

    fireEvent.click(screen.getAllByText("Clear filters")[0]);
    expect(within(screen.getByRole("table")).getByText("PLTR")).toBeInTheDocument();
  });

  it("navigates to the ticker's screener detail route on row click", () => {
    renderTable();
    fireEvent.click(screen.getByText("PLTR"));
    expect(navigateMock).toHaveBeenCalledWith("/screener/PLTR");
  });

  it("keeps a sort applied via external viewState across an unmount/remount (simulating list -> detail -> back)", () => {
    // Mirrors what ScreenerSection does: state lives above the table, so it
    // outlives ScreenerTable unmounting when navigating to a detail route.
    function Harness({ mounted }) {
      const [sort, setSort] = useState(null);
      const [filters, setFilters] = useState(EMPTY_FILTER_STATE);
      return mounted ? (
        <MemoryRouter>
          <ScreenerTable results={RESULTS} viewState={{ sort, setSort, filters, setFilters }} />
        </MemoryRouter>
      ) : null;
    }

    const { rerender } = render(<Harness mounted={true} />);
    fireEvent.click(screen.getByText("Price"));
    let tickerCells = screen.getAllByRole("row").slice(1).map((r) => r.querySelector("td").textContent);
    expect(tickerCells[0]).toContain("ZZZZ"); // lowest price first, asc

    rerender(<Harness mounted={false} />); // simulates navigating to /screener/:ticker
    rerender(<Harness mounted={true} />); // simulates navigating back to /screener

    tickerCells = screen.getAllByRole("row").slice(1).map((r) => r.querySelector("td").textContent);
    expect(tickerCells[0]).toContain("ZZZZ"); // sort survived the round trip
  });
});
