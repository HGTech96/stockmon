/**
 * @param {{ title: string, subtitle?: string, children: import('react').ReactNode }} props
 * The bordered, shadowed card shell used for every detail-page section
 * (`.panel` in the reference) -- title row + content. Shared so Portfolio's
 * future panels reuse the same chrome instead of re-implementing it.
 */
export function Panel({ title, subtitle, children }) {
  return (
    <div className="rounded-DEFAULT border border-border bg-surface p-5 shadow-card">
      <div className="mb-3.5 flex items-center justify-between text-[13.5px] font-bold">
        <span>{title}</span>
        {subtitle && <span className="text-xs font-medium text-ink-muted">{subtitle}</span>}
      </div>
      {children}
    </div>
  );
}
