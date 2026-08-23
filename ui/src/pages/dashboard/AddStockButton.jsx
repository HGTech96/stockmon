/**
 * @param {{ onClick: () => void }} props
 * Opens the add-stock modal. Raw-Tailwind styling matching RefreshButton's
 * secondary-button pattern (not the shadcn Button primitive), sitting
 * beside it above the dashboard table.
 */
export function AddStockButton({ onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-lg border border-border-strong bg-surface px-4 py-2.5 text-[13.5px] font-semibold text-ink hover:bg-surface-sunken"
    >
      Add
    </button>
  );
}
