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
