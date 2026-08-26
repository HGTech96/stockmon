import { request } from "./client";

/** @returns {Promise<import('./types').ScreenerResponse>} */
export function getScreener() {
  return request("/screener");
}

/**
 * @param {string} ticker
 * @returns {Promise<import('./types').StockDetailResponse>}
 */
export function getScreenerDetail(ticker) {
  return request(`/screener/${ticker}/detail`);
}

/** @returns {Promise<import('./types').ScreenerRefreshResponse>} */
export function postScreenerRefresh() {
  return request("/screener/refresh", { method: "POST" });
}
