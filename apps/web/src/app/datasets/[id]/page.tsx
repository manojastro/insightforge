"use client";

import { use, useEffect, useState } from "react";
import { getDataset, getApiErrorMessage } from "@/lib/api";
import type { DatasetDetail } from "@/lib/types";
import DataTable from "@/components/DataTable";
import ChartRenderer from "@/components/ChartRenderer";

export default function DatasetDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [ds, setDs] = useState<DatasetDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const d = await getDataset(id);
        if (live) setDs(d);
      } catch (e) {
        if (live) setError(getApiErrorMessage(e));
      } finally {
        if (live) setLoading(false);
      }
    })();
    return () => {
      live = false;
    };
  }, [id]);

  if (loading) return <p className="text-sm text-slate-500">Loading dataset {id}…</p>;
  if (error)
    return (
      <p className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">
        {error}
      </p>
    );
  if (!ds) return <p className="text-sm">Dataset not found.</p>;

  const missingChart = {
    kind: "bar" as const,
    title: "Missing values by column",
    xKey: "column",
    yKey: "missingPct",
    data: ds.profile.missingByColumn.map((m) => ({
      column: m.column,
      missingPct: m.missingPct,
      missingCount: m.missingCount,
    })),
  };

  const firstDist = ds.profile.distributions[0];
  const distChart = firstDist
    ? {
        kind: "bar" as const,
        title: `Distribution: ${firstDist.column}`,
        xKey: "label",
        yKey: "count",
        data: (firstDist.bins ?? []).map((b) => ({ label: b.label, count: b.count })),
      }
    : null;

  const cols = ds.sampleRows[0] ? Object.keys(ds.sampleRows[0]) : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold">{ds.name}</h1>
        <p className="text-sm text-slate-500">
          {ds.rowCount.toLocaleString()} rows · {ds.colCount} cols · quality{" "}
          {(ds.profile.quality.overall * 100).toFixed(1)}%
        </p>
      </div>

      {ds.profile.piiWarnings.length > 0 && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
          <h2 className="font-semibold text-amber-900 dark:text-amber-100">PII warnings</h2>
          <ul className="mt-1 list-disc pl-5 text-sm">
            {ds.profile.piiWarnings.map((w, i) => (
              <li key={i}>
                <code>{w.column}</code> — {w.piiType} ({w.count} values
                {w.sampleMasked ? `, e.g. ${w.sampleMasked}` : ""})
              </li>
            ))}
          </ul>
        </div>
      )}

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {(
          [
            ["Completeness", ds.profile.quality.completeness],
            ["Validity", ds.profile.quality.validity],
            ["Uniqueness", ds.profile.quality.uniqueness],
            ["Consistency", ds.profile.quality.consistency],
            ["Overall", ds.profile.quality.overall],
          ] as Array<[string, number]>
        ).map(([k, v]) => (
          <div key={k} className="rounded-lg border p-3 dark:border-slate-800">
            <div className="text-xs text-slate-500">{k}</div>
            <div className="text-lg font-bold">{(v * 100).toFixed(1)}%</div>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border p-4 dark:border-slate-800">
          <ChartRenderer chart={missingChart} height={260} />
        </div>
        <div className="rounded-lg border p-4 dark:border-slate-800">
          {distChart ? (
            <ChartRenderer chart={distChart} height={260} />
          ) : (
            <p className="text-sm text-slate-500">No distributions available.</p>
          )}
        </div>
      </section>

      <section className="rounded-lg border dark:border-slate-800">
        <h2 className="border-b p-3 font-semibold dark:border-slate-800">Schema</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900">
              <tr>
                <th className="px-3 py-2 text-left">Column</th>
                <th className="px-3 py-2 text-left">Type</th>
                <th className="px-3 py-2 text-right">Missing %</th>
                <th className="px-3 py-2 text-right">Unique</th>
                <th className="px-3 py-2 text-left">PII</th>
              </tr>
            </thead>
            <tbody>
              {ds.schema.map((c) => (
                <tr key={c.name} className="border-t dark:border-slate-800">
                  <td className="px-3 py-1.5 font-mono">{c.name}</td>
                  <td className="px-3 py-1.5">{c.dtype}</td>
                  <td className="px-3 py-1.5 text-right">
                    {c.missingPct != null ? `${(c.missingPct * 100).toFixed(1)}%` : "—"}
                  </td>
                  <td className="px-3 py-1.5 text-right">{c.uniqueCount ?? "—"}</td>
                  <td className="px-3 py-1.5">{c.isPii ? `yes (${c.piiType})` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-semibold">Sample data</h2>
        {ds.sampleRows.length === 0 ? (
          <p className="text-sm text-slate-500">No sample rows.</p>
        ) : (
          <DataTable columns={cols} rows={ds.sampleRows} />
        )}
      </section>
    </div>
  );
}
