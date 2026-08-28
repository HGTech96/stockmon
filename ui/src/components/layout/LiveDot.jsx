import { motion, useReducedMotion } from "motion/react";

/**
 * Pulsing status dot -- the persistent "this data is live" cue.
 * @param {{ tone?: "good"|"warn" }} props
 */
export function LiveDot({ tone = "good" }) {
  const reduceMotion = useReducedMotion();
  const color = tone === "good" ? "var(--color-good)" : "var(--color-warn)";

  return (
    <span className="relative flex h-[7px] w-[7px] flex-none">
      {!reduceMotion && (
        <motion.span
          className="absolute inline-flex h-full w-full rounded-full"
          style={{ backgroundColor: color }}
          animate={{ scale: [1, 2.4], opacity: [0.55, 0] }}
          transition={{ duration: 1.8, repeat: Infinity, ease: "easeOut" }}
        />
      )}
      <span className="relative inline-flex h-[7px] w-[7px] rounded-full" style={{ backgroundColor: color }} />
    </span>
  );
}
