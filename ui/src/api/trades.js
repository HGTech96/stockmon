import { request } from "./client";

/**
 * @param {import('./types').TradeRequest} payload
 * @returns {Promise<import('./types').TradeResponse>}
 */
export function postTrade(payload) {
  return request("/trades", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** @returns {Promise<import('./types').TradesResponse>} */
export function getTrades() {
  return request("/trades");
}

/**
 * @param {number} id
 * @param {import('./types').TradeUpdateRequest} payload
 * @returns {Promise<import('./types').TradeResponse>}
 */
export function putTrade(id, payload) {
  return request(`/trades/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/** @param {number} id */
export function deleteTrade(id) {
  return request(`/trades/${id}`, { method: "DELETE" });
}
