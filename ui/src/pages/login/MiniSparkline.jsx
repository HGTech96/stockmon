import { useRef } from "react";
import { useGSAP } from "@gsap/react";
import gsap from "gsap";

function buildPaths(values, width, height, padding) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const stepX = (width - padding * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = padding + i * stepX;
    const y = padding + (1 - (v - min) / range) * (height - padding * 2);
    return [x, y];
  });

  const line = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(2)},${y.toFixed(2)}`).join(" ");
  const [firstX] = points[0];
  const [lastX] = points[points.length - 1];
  const area = `${line} L${lastX.toFixed(2)},${height} L${firstX.toFixed(2)},${height} Z`;

  return { line, area };
}

/**
 * Draws itself in on mount via GSAP (stroke-dashoffset) -- a load-sequence
 * animation, not scroll-tied, but GSAP owns it here for the same
 * timeline-choreography reason ScrollTrigger hero sequences do. Reduced-
 * motion users get the finished state instantly.
 */
export function MiniSparkline({ values, width = 420, height = 110, stroke = "var(--color-accent)" }) {
  const lineRef = useRef(null);
  const areaRef = useRef(null);
  const gradientId = useRef(`sparkline-fill-${Math.random().toString(36).slice(2)}`).current;
  const { line, area } = buildPaths(values, width, height, 4);

  useGSAP(() => {
    const path = lineRef.current;
    const fill = areaRef.current;
    if (!path || !fill) return;

    const length = path.getTotalLength();
    const mm = gsap.matchMedia();

    mm.add(
      { reduce: "(prefers-reduced-motion: reduce)", noReduce: "(prefers-reduced-motion: no-preference)" },
      (ctx) => {
        const { reduce } = ctx.conditions;
        if (reduce) {
          gsap.set(path, { strokeDasharray: length, strokeDashoffset: 0 });
          gsap.set(fill, { opacity: 1 });
          return;
        }
        gsap.set(path, { strokeDasharray: length, strokeDashoffset: length });
        gsap.set(fill, { opacity: 0 });
        gsap.to(path, { strokeDashoffset: 0, duration: 1.3, ease: "power3.out", delay: 0.15 });
        gsap.to(fill, { opacity: 1, duration: 0.9, ease: "power2.out", delay: 0.55 });
      },
    );

    return () => mm.revert();
  }, [line]);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-auto w-full overflow-visible" aria-hidden="true">
      <defs>
        <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.35" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path ref={areaRef} d={area} fill={`url(#${gradientId})`} stroke="none" />
      <path ref={lineRef} d={line} fill="none" stroke={stroke} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
