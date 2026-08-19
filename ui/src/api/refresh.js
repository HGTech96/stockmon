import { request } from "./client";

/** @returns {Promise<import('./types').RefreshResponse>} */
export function postRefresh() {
  return request("/refresh", { method: "POST" });
}
