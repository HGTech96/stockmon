import { request } from "./client";

/**
 * @param {import('./types').CashEventRequest} payload
 * @returns {Promise<import('./types').CashEventResponse>}
 */
export function postCashEvent(payload) {
  return request("/cash", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
