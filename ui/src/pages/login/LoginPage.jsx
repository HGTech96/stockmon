import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { useAuth } from "../../hooks/useAuth";
import { LiveMarketPanel } from "./LiveMarketPanel";

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [showReset, setShowReset] = useState(false);

  // Already signed in (e.g. navigated here directly) -- nothing to do here.
  if (user) return <Navigate to="/" replace />;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError("Enter your username and password.");
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await login(username.trim(), password);
      navigate("/", { replace: true });
    } catch (err) {
      setError(err.message ?? "Couldn't sign in.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-surface">
      <div className="noise-overlay" aria-hidden="true" />

      {/* Story panel: the login screen behaves like a miniature dashboard, ticking live,
          so the product's value is visible before you're even signed in. */}
      <div className="relative hidden w-[56%] flex-col justify-between overflow-hidden bg-ink px-14 py-12 text-white lg:flex">
        <div
          className="pointer-events-none absolute inset-0"
          style={{ background: "radial-gradient(60% 50% at 12% 0%, rgba(8,145,178,0.18), transparent 60%)" }}
          aria-hidden="true"
        />

        <div className="relative flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
          <span className="text-[15px] font-bold tracking-tight">stockmon</span>
        </div>

        <div className="relative flex max-w-[440px] flex-col gap-8">
          <div>
            <p className="mb-3 text-[12px] font-semibold tracking-[0.14em] text-accent uppercase">Portfolio monitor</p>
            <h1 className="text-[40px] leading-[1.08] font-bold tracking-tight">
              Every position,
              <br />
              one clear signal.
            </h1>
            <p className="mt-4 text-[14px] text-white/55">
              stockmon watches your watchlist around the clock and tells you when a position is worth a second
              look — no noise, no doomscrolling a ticker.
            </p>
          </div>

          <LiveMarketPanel />
        </div>

        <p className="relative text-[12px] text-white/35">Prices shown are illustrative for this design preview.</p>
      </div>

      {/* Form panel */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-16 lg:w-[44%]">
        <div className="w-full max-w-[360px]">
          <img src="/full-logo.svg" alt="stockmon" className="h-7 w-auto" />

          <div className="mt-10 mb-7">
            <h2 className="text-2xl font-bold tracking-tight text-ink">Sign in</h2>
            <p className="mt-1.5 text-[13px] text-ink-muted">Welcome back — your watchlist is right where you left it.</p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            <label className="flex flex-col gap-1.5">
              <span className="text-[12px] font-semibold text-ink-muted">Username</span>
              <input
                type="text"
                autoFocus
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="rounded-sm border border-border-strong bg-surface-sunken px-3 py-2.5 text-[13.5px] text-ink placeholder:text-ink-faint focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none"
              />
            </label>

            <label className="flex flex-col gap-1.5">
              <span className="text-[12px] font-semibold text-ink-muted">Password</span>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-sm border border-border-strong bg-surface-sunken px-3 py-2.5 pr-9 text-[13.5px] text-ink placeholder:text-ink-faint focus:border-accent focus:ring-1 focus:ring-accent focus:outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute top-1/2 right-2.5 -translate-y-1/2 text-ink-faint hover:text-ink"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" strokeWidth={1.8} /> : <Eye className="h-4 w-4" strokeWidth={1.8} />}
                </button>
              </div>
            </label>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-[12.5px] font-medium text-ink-muted">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  style={{ accentColor: "var(--color-accent)" }}
                  className="h-3.5 w-3.5"
                />
                Remember me
              </label>
              <button
                type="button"
                onClick={() => setShowReset((s) => !s)}
                className="text-[12.5px] font-semibold text-accent-ink hover:underline"
              >
                Forgot password?
              </button>
            </div>

            {showReset && (
              <p className="rounded-sm border border-accent-border bg-accent-soft px-3 py-2 text-[12.5px] text-accent-ink">
                Password resets aren't self-service yet — ask whoever set up your account to reset it for you.
              </p>
            )}

            {error && <p className="text-[12.5px] font-semibold text-bad">{error}</p>}

            <Button type="submit" variant="primary" size="lg" disabled={submitting} className="mt-1 w-full justify-center">
              {submitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" strokeWidth={2.5} />
                  Signing in…
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
