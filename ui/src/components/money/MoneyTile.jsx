const TONE_TEXT = {
  neutral: "text-ink",
  good: "text-good",
  bad: "text-bad",
};

const TONE_BG = {
  neutral: "",
  good: "bg-good-bg",
  bad: "bg-warn-bg",
};

/**
 * @param {{ label: string, value: string, sub?: string, tone?: "neutral"|"good"|"bad", live?: boolean }} props
 * One stat cell inside a MoneyCluster. `tone` only colors the value when
 * non-zero (callers pass "neutral" for a $0.00 figure so it stays plain
 * ink, per the phase 9b design decision -- zero is calm, not emphasized).
 * `live` washes the cell in a faint tint of its tone -- only meaningful
 * paired with a non-neutral tone, used for the Unrealized cluster's
 * "still moving" signal. `flex-1` (equal width in the parent's flex row)
 * combined with flex's default height-stretch is what makes the tint
 * cover the entire cell rather than just the text's own height -- see
 * MoneyCluster's doc comment.
 */
export function MoneyTile({ label, value, sub, tone = "neutral", live = false }) {
  return (
    <div className={`flex-1 px-5 py-4 ${live ? TONE_BG[tone] : "bg-surface"}`}>
      <div className="mb-1.5 text-xs font-semibold text-ink-muted">{label}</div>
      <div className={`num text-[20px] font-semibold tracking-tight ${TONE_TEXT[tone]}`}>{value}</div>
      {sub && <div className="mt-0.5 text-[12.5px] text-ink-muted">{sub}</div>}
    </div>
  );
}
