import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { fmtRelativeTime } from "./format";

describe("fmtRelativeTime", () => {
  const NOW = new Date("2026-08-24T12:00:00-04:00");

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns 'Just now' for under a minute", () => {
    expect(fmtRelativeTime(new Date(NOW.getTime() - 30_000).toISOString())).toBe("Just now");
  });

  it("returns minutes ago under an hour", () => {
    expect(fmtRelativeTime(new Date(NOW.getTime() - 5 * 60_000).toISOString())).toBe("5m ago");
  });

  it("returns hours ago under a day", () => {
    expect(fmtRelativeTime(new Date(NOW.getTime() - 3 * 60 * 60_000).toISOString())).toBe("3h ago");
  });

  it("returns days ago at a day or more", () => {
    expect(fmtRelativeTime(new Date(NOW.getTime() - 2 * 24 * 60 * 60_000).toISOString())).toBe("2d ago");
  });

  it("floors partial units", () => {
    expect(fmtRelativeTime(new Date(NOW.getTime() - 89 * 60_000).toISOString())).toBe("1h ago");
  });
});
