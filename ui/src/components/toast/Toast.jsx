import { AnimatePresence, motion } from "motion/react";

const TONE_CLASSES = {
  good: "border-good-border bg-good-bg text-good",
  neutral: "border-neutral-border bg-neutral-bg text-neutral",
};

/**
 * @param {{ message: string | null, tone?: "good" | "neutral" }} props
 * Single top-right toast. Scoped to the add-stock feature -- not retrofitted
 * elsewhere. Renders nothing when there's no message. "good" (green) for an
 * actual add; "neutral" (gray) for the already-on-watchlist notice, which
 * isn't a success and shouldn't read as one.
 */
export function Toast({ message, tone = "good" }) {
  return (
    <AnimatePresence>
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -8, scale: 0.97 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -8, scale: 0.97 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
          className={`fixed top-5 right-5 z-50 rounded-DEFAULT border px-4 py-2.5 text-[13px] font-medium shadow-pop ${TONE_CLASSES[tone]}`}
        >
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
