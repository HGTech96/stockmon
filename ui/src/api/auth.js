import { request } from "./client";

/**
 * @param {string} username
 * @param {string} password
 * @returns {Promise<import('./types').User>}
 */
export function login(username, password) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

/** @returns {Promise<void>} */
export function logout() {
  return request("/auth/logout", { method: "POST" });
}

/** @returns {Promise<import('./types').User>} */
export function getCurrentUser() {
  return request("/auth/me");
}
