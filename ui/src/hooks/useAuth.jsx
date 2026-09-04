import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getCurrentUser, login as loginRequest, logout as logoutRequest } from "../api/auth";
import { setUnauthorizedHandler } from "../api/client";

const AuthContext = createContext(null);

/**
 * The one sanctioned context in this app (see CLAUDE.md's "no context
 * unless unavoidable") -- session state is read by the route guard and the
 * header's user menu, both far from wherever a fetch might 401.
 *
 * On mount, checks for an existing session via GET /api/auth/me. Also
 * registers as the app-wide 401 handler (see api/client.js) so a session
 * that dies mid-use (expiry, server restart) logs the UI out immediately
 * instead of pages quietly failing.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setUnauthorizedHandler(() => setUser(null));
    getCurrentUser()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      async login(username, password) {
        const loggedInUser = await loginRequest(username, password);
        setUser(loggedInUser);
        return loggedInUser;
      },
      async logout() {
        await logoutRequest();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
