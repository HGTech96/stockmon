import { request } from "./client";

/** @returns {Promise<import('./types').DashboardResponse>} */
export function getStocks() {
  return request("/stocks");
}

/**
 * @param {string} ticker
 * @returns {Promise<import('./types').StockDetailResponse>}
 */
export function getStockDetail(ticker) {
  return request(`/stocks/${ticker}`);
}

/**
 * @param {string} ticker
 * @returns {Promise<import('./types').AddStockResponse>}
 */
export function addStock(ticker) {
  return request("/stocks", { method: "POST", body: JSON.stringify({ ticker }) });
}
