const BASE_URL = "/api";

/**
 * Shared fetch wrapper. Vite's dev server proxies /api to the FastAPI
 * backend (see vite.config.js), so this is a relative path in both dev
 * and prod. Throws with the contract's `{ "error": "..." }` message on
 * a non-2xx response.
 *
 * @param {string} path - e.g. "/stocks"
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
async function request(path, options) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (res.status === 204) return null;
  const body = await res.json();
  if (!res.ok) {
    throw new Error(body.error ?? "Request failed");
  }
  return body;
}

export { request };
