import type { Plan } from "@/lib/types";

interface Meta {
  durationMs?: number;
  rowCount?: number;
  intermediate?: Array<{ label: string; rowCount: number; durationMs?: number }>;
  chartConfig?: Record<string, string | number | boolean>;
}

export default function PlanViewer({ plan, meta }: { plan?: Plan; meta?: Meta }) {
  if (!plan || plan.steps.length === 0) return <p className="text-sm text-slate-500">No plan available.</p>;
  return (
    <div className="space-y-3">
      {plan.reasoningSummary && (
        <p className="rounded bg-slate-50 p-2.5 text-sm dark:bg-slate-900">{plan.reasoningSummary}</p>
      )}
      {meta && (
        <div className="flex flex-wrap gap-2 text-xs text-slate-500">
          {meta.durationMs != null && <span className="rounded border px-2 py-1 dark:border-slate-700">duration: {meta.durationMs} ms</span>}
          {meta.rowCount != null && <span className="rounded border px-2 py-1 dark:border-slate-700">rows: {meta.rowCount}</span>}
          {plan.estimatedCost && <span className="rounded border px-2 py-1 dark:border-slate-700">cost: {plan.estimatedCost}</span>}
        </div>
      )}
      <ol className="space-y-2">
        {plan.steps.map((s) => (
          <li key={s.id} className="rounded-lg border p-3 text-sm dark:border-slate-800">
            <div className="flex items-center gap-2">
              <span
                className={`rounded px-1.5 py-0.5 text-[11px] font-semibold ${
                  s.status === "failed"
                    ? "bg-red-100 text-red-800"
                    : s.status === "done"
                      ? "bg-green-100 text-green-800"
                      : s.status === "running"
                        ? "bg-blue-100 text-blue-800"
                        : "bg-slate-100 text-slate-600"
                }`}
              >
                {s.status ?? s.kind}
              </span>
              <span className="font-medium">{s.title}</span>
            </div>
            {s.detail && <p className="mt-1 text-xs text-slate-500">{s.detail}</p>}
          </li>
        ))}
      </ol>
      {meta?.intermediate && meta.intermediate.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold uppercase text-slate-500">Intermediate results</h4>
          <ul className="mt-1 space-y-1 text-xs">
            {meta.intermediate.map((r, i) => (
              <li key={i} className="rounded border px-2 py-1 dark:border-slate-700">
                {r.label} — {r.rowCount} rows{r.durationMs != null ? ` · ${r.durationMs} ms` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
      {meta?.chartConfig && (
        <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-[11px] text-slate-200">
          chart: {JSON.stringify(meta.chartConfig, null, 2)}
        </pre>
      )}
    </div>
  );
}
