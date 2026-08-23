import { useCallback, useRef, useState } from "react";

const AUTO_DISMISS_MS = 4000;

/**
 * Minimal local-state toast, scoped to the add-stock feature only -- not a
 * shared app-wide toast system. show() replaces any currently-showing
 * toast and resets the auto-dismiss timer.
 * @returns {{ message: string|null, tone: "good"|"neutral", show: (message: string, tone?: "good"|"neutral") => void }}
 */
export function useToast() {
  const [message, setMessage] = useState(null);
  const [tone, setTone] = useState("good");
  const timeoutRef = useRef(null);

  const show = useCallback((next, nextTone = "good") => {
    clearTimeout(timeoutRef.current);
    setMessage(next);
    setTone(nextTone);
    timeoutRef.current = setTimeout(() => setMessage(null), AUTO_DISMISS_MS);
  }, []);

  return { message, tone, show };
}
