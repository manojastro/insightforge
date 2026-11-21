"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { healthz, listDatasets, getApiErrorMessage } from "@/lib/api";
import type { Dataset } from "@/lib/types";
import KpiCard from "@/components/KpiCard";

function qualityOf(d: Dataset): number {
  return typeof d.quality === "number" ? d.quality : d.quality.overall;
}

export default function HomePage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [apiStatus, setApiStatus] = useState<string>("checking…");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const h = await healthz();
        if (live) setApiStatus(h.status ?? "ok");
      } catch (e) {
        if (live) setApiStatus("unreachable: " + getApiErrorMessage(e));
      }
      try {
        const ds = await listDatasets();
        if (live) setDatasets(ds);
      } catch (e) {
        if (live) setError(getApiErrorMessage(e));
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  const totalRows = datasets.reduce((a, d) => a + (d.rowCount || 0), 0);
  const avgQuality =
    datasets.length > 0
      ? datasets.reduce((a, d) => a + qualityOf(d), 0) / datasets.length
      : 0;
  const piiCount = datasets.reduce((a, d) => a + (d.piiWarnings?.length ?? 0), 0);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Ask questions of your data</h1>
          <p className="mt-1 text-sm text-slate-500">
            Verified SQL, charts, and cited evidence. API: {apiStatus}
          </p>
          {error && (
            <p className="mt-2 rounded bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">
              {error} — showing empty state.
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <Link
            href="/analysis"
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Try a demo question
          </Link>
          <Link
            href="/datasets"
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Browse datasets
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard label="Datasets" value={String(datasets.length)} />
        <KpiCard label="Total rows" value={totalRows.toLocaleString()} />
        <KpiCard label="Avg quality" value={`${(avgQuality * 100).toFixed(1)}%`} />
        <KpiCard label="PII warnings" value={String(piiCount)} />
      </div>

      <div className="rounded-lg border border-slate-200 p-4 dark:border-slate-800">
        <h2 className="font-semibold">How it works</h2>
        <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-600 dark:text-slate-300">
          <li>Upload or connect a dataset (Datasets page).</li>
          <li>Ask a question — the agent plans, writes SQL, and runs it in a sandbox.</li>
          <li>Inspect Show My Work: plan, SQL, duration, row counts, evidence.</li>
          <li>Save insights and export an executive report.</li>
        </ol>
      </div>
    </div>
  );
}
