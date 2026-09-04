import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { ChevronDown, LogOut, Settings } from "lucide-react";

function initialsFor(username) {
  return username.slice(0, 2).toUpperCase();
}

/**
 * @param {{ user: import('../../api/types').User, onLogout: () => void, onAccountSettings: () => void }} props
 */
export function UserMenu({ user, onLogout, onAccountSettings }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) return;
    function handlePointer(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false);
    }
    function handleKey(e) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointer);
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("mousedown", handlePointer);
      document.removeEventListener("keydown", handleKey);
    };
  }, [open]);

  return (
    <div className="relative" ref={rootRef}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="menu"
        aria-expanded={open}
        className="flex items-center gap-1.5 rounded-sm py-1 pr-1.5 pl-1 transition-colors hover:bg-surface-hover"
      >
        <span className="flex h-7 w-7 flex-none items-center justify-center rounded-full bg-accent-soft text-[11px] font-bold text-accent-ink">
          {initialsFor(user.username)}
        </span>
        <ChevronDown
          className={`h-3.5 w-3.5 text-ink-faint transition-transform duration-150 ${open ? "rotate-180" : ""}`}
          strokeWidth={2}
        />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            role="menu"
            initial={{ opacity: 0, y: -6, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.97 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
            className="absolute top-[calc(100%+8px)] right-0 z-50 w-56 rounded-DEFAULT border border-border-strong bg-surface p-1.5 shadow-pop"
          >
            <div className="px-2.5 py-2">
              <p className="truncate text-[13px] font-semibold text-ink">{user.username}</p>
              {user.email && <p className="truncate text-[12px] text-ink-muted">{user.email}</p>}
            </div>
            <div className="my-1 h-px bg-border" />
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                onAccountSettings();
              }}
              className="flex w-full items-center gap-2.5 rounded-sm px-2.5 py-2 text-left text-[13px] font-medium text-ink hover:bg-surface-hover"
            >
              <Settings className="h-4 w-4 text-ink-faint" strokeWidth={1.8} />
              Account settings
            </button>
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                onLogout();
              }}
              className="flex w-full items-center gap-2.5 rounded-sm px-2.5 py-2 text-left text-[13px] font-medium text-bad hover:bg-bad-bg"
            >
              <LogOut className="h-4 w-4" strokeWidth={1.8} />
              Log out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
