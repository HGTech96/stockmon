const BASE_URL = "/api";

// Set by useAuth so any request anywhere in the app that comes back 401
// (session missing/expired) immediately clears the logged-in user, which
// sends the route guard back to /login -- without this, a page could keep
// rendering as if still authenticated after the session died server-side.
let onUnauthorized = null;

/** @param {() => void} handler */
function setUnauthorizedHandler(handler) {
  onUnauthorized = handler;
}

/**
 * Shared fetch wrapper. Vite's dev server proxies /api to the FastAPI
 * backend (see vite.config.js), so this is a relative path in both dev
 * and prod. Throws with the contract's `{ "error": "..." }` message on
 * a non-2xx response. `credentials: "include"` sends/receives the session
 * cookie even if the UI and API ever end up on different origins.
 *
 * @param {string} path - e.g. "/stocks"
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
async function request(path, options) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...options,
  });
  if (res.status === 401) onUnauthorized?.();
  if (res.status === 204) return null;
  const body = await res.json();
  if (!res.ok) {
    const err = new Error(body.error ?? "Request failed");
    err.status = res.status;
    throw err;
  }
  return body;
}

export { request, setUnauthorizedHandler };
