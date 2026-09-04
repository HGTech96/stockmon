import { Navigate } from "react-router-dom";
import { useAuth } from "../../hooks/useAuth";

/**
 * Route guard wrapping every page except /login. Renders nothing while the
 * initial GET /api/auth/me check is in flight (avoids a login-page flash
 * for an already-logged-in user on reload).
 */
export function RequireAuth({ children }) {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}
