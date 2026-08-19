import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { postRefresh } from "../api/refresh";

/**
 * yfinance data is itself delayed up to 15 minutes, so polling the backend
 * faster than that would just be wasted calls -- 15 minutes is the fastest
 * interval that can ever surface new data.
 */
const REFRESH_INTERVAL_MS = 15 * 60 * 1000;

/**
 * Runs POST /api/refresh on a fixed interval, then invalidates every
 * TanStack Query cache entry so mounted pages refetch with fresh data.
 * Mounted once in AppShell -- there is no server "isRefreshing" state,
 * the client is simply awaiting this POST.
 */
export function useDataRefresh() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const id = setInterval(async () => {
      await postRefresh();
      queryClient.invalidateQueries();
    }, REFRESH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [queryClient]);
}
