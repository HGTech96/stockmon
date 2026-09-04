import { useEffect, useRef, useState } from "react";
import { animate, useReducedMotion } from "motion/react";

/**
 * Tweens a numeric value on change so live price/P&L updates count rather
 * than jump.
 * @param {number} value
 * @param {number} [duration]
 * @returns {number}
 */
export function useTweenedNumber(value, duration = 0.6) {
  const [display, setDisplay] = useState(value);
  const prevRef = useRef(value);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (prevRef.current === value) return;
    if (reduceMotion) {
      prevRef.current = value;
      setDisplay(value);
      return;
    }
    const from = prevRef.current;
    prevRef.current = value;
    const controls = animate(from, value, {
      duration,
      ease: "easeOut",
      onUpdate: (latest) => setDisplay(latest),
    });
    return () => controls.stop();
  }, [value, duration, reduceMotion]);

  return display;
}
