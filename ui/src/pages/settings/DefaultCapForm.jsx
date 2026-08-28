import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { putSettings } from "../../api/settings";

const fieldClass =
  "rounded-lg border border-border-strong bg-surface px-3 py-2.5 text-[13.5px] text-ink focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent";

/**
 * @param {{ defaultProfitTargetDollars: number, onSaved: () => void }} props
 * The caller keys this component on `defaultProfitTargetDollars` so a
 * changed value (e.g. after saving) remounts it with a fresh initial
 * state, rather than syncing via an effect.
 */
export function DefaultCapForm({ defaultProfitTargetDollars, onSaved }) {
  const [value, setValue] = useState(String(defaultProfitTargetDollars));

  const mutation = useMutation({
    mutationFn: () => putSettings({ defaultProfitTargetDollars: Number(value) }),
    onSuccess: onSaved,
  });

  return (
    <div className="mb-8 max-w-[420px] rounded-DEFAULT border border-border bg-surface p-5">
      <h2 className="mb-1 text-[14px] font-bold">Default hard cap</h2>
      <p className="mb-4 text-[12.5px] text-ink-muted">
        Applies to any owned stock without its own hard cap set below.
      </p>
      <form
        className="flex items-end gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor="default-cap" className="text-[12.5px] font-bold text-ink-muted">
            Amount
          </label>
          <input
            id="default-cap"
            type="number"
            className={`num ${fieldClass}`}
            min="0.01"
            step="0.01"
            required
            value={value}
            onChange={(e) => setValue(e.target.value)}
            disabled={mutation.isPending}
          />
        </div>
        <button
          type="submit"
          disabled={mutation.isPending}
          className="rounded-lg border border-accent bg-accent px-4 py-2.5 text-[13.5px] font-semibold text-white hover:bg-accent-ink disabled:opacity-50"
        >
          {mutation.isPending ? "Saving…" : "Save"}
        </button>
      </form>
      {mutation.isError && (
        <div className="mt-3 rounded-lg border border-warn-border bg-warn-bg px-3 py-2.5 text-[13px] text-warn">
          {mutation.error.message}
        </div>
      )}
    </div>
  );
}
