import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getSettings } from "../../api/settings";
import { DefaultCapForm } from "./DefaultCapForm";
import { OverridesList } from "./OverridesList";

function invalidateAfterCapChange(queryClient) {
  queryClient.invalidateQueries({ queryKey: ["settings"] });
  queryClient.invalidateQueries({ queryKey: ["stocks"] });
  queryClient.invalidateQueries({ queryKey: ["portfolio"] });
  queryClient.invalidateQueries({ queryKey: ["stock"] });
}

export function SettingsPage() {
  const queryClient = useQueryClient();
  const { data, error, isPending } = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  if (isPending) {
    return <p className="py-20 text-center text-ink-muted">Loading…</p>;
  }

  if (error) {
    return <p className="py-20 text-center text-bad">{error.message}</p>;
  }

  return (
    <div>
      <div className="mb-5">
        <h1 className="text-xl font-bold tracking-tight">Settings</h1>
      </div>

      <DefaultCapForm
        key={data.defaultProfitTargetDollars}
        defaultProfitTargetDollars={data.defaultProfitTargetDollars}
        onSaved={() => invalidateAfterCapChange(queryClient)}
      />

      <OverridesList
        perPositionTargets={data.perPositionTargets}
        onReset={() => invalidateAfterCapChange(queryClient)}
      />
    </div>
  );
}
