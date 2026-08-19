import { useEffect } from "react";
import { useOutletContext } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getPortfolio } from "../../api/portfolio";

/**
 * Placeholder for Phase 5. Proves the query/CORS/freshness wiring works
 * end-to-end: shows a loading state, the error message on failure, and a
 * raw JSON dump of the response on success.
 */
export function PortfolioPage() {
  const { setMeta } = useOutletContext();
  const { data, error, isPending } = useQuery({
    queryKey: ["portfolio"],
    queryFn: getPortfolio,
  });

  useEffect(() => {
    setMeta(data?.meta);
  }, [data, setMeta]);

  return (
    <div>
      <h1 className="mb-4 text-xl font-bold tracking-tight">Portfolio</h1>
      {isPending && <p className="text-ink-muted">Loading...</p>}
      {error && <p className="text-bad">{error.message}</p>}
      {data && (
        <pre className="num overflow-x-auto rounded border border-border bg-surface-sunken p-4 text-xs">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}
