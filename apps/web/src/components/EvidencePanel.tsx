import type { Evidence } from "@/lib/types";

export default function EvidencePanel({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) return <p className="text-sm text-slate-500">No evidence cited.</p>;
  return (
    <ul className="space-y-2">
      {evidence.map((e) => (
        <li key={e.id} className="rounded-lg border p-3 text-sm dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] font-semibold text-slate-600 dark:bg-slate-800 dark:text-slate-300">
              {e.kind}
            </span>
            <span className="font-medium">{e.label}</span>
          </div>
          {e.detail && <p className="mt-1 text-xs text-slate-500">{e.detail}</p>}
          {e.rowIds && e.rowIds.length > 0 && (
            <p className="mt-1 font-mono text-[11px] text-slate-400">rows: {e.rowIds.slice(0, 8).join(", ")}{e.rowIds.length > 8 ? "…" : ""}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
