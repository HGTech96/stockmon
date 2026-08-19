import { request } from "./client";

/** @returns {Promise<import('./types').PortfolioResponse>} */
export function getPortfolio() {
  return request("/portfolio");
}
