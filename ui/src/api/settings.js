import { request } from "./client";

/** @returns {Promise<import('./types').Settings>} */
export function getSettings() {
  return request("/settings");
}

/**
 * @param {{ defaultProfitTargetDollars: number }} payload
 * @returns {Promise<import('./types').Settings>}
 */
export function putSettings(payload) {
  return request("/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/**
 * @param {string} ticker
 * @param {{ targetDollars: number }} payload
 * @returns {Promise<import('./types').Settings>}
 */
export function putPositionTarget(ticker, payload) {
  return request(`/settings/targets/${ticker}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
