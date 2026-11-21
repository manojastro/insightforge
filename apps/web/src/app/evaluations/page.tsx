"use client";

import { useEffect, useState } from "react";
import { getEvalSummary, getApiErrorMessage } from "@/lib/api";
import type { EvalSummary } from "@/lib/types";
import ChartRenderer from "@/components/ChartRenderer";
import KpiCard from "@/components/KpiCard";

export default function EvaluationsPage() {
  const [data, setData] = useState<EvalSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    (async () => {
      try {
        const s = await getEvalSummary();
        if (live) setData(s);
      } catch (e) {
        if (live) setError(getApiErrorMessage(e));
      }
    })();
    return () => {
      live = false;
    };
  }, []);

  if (error)
    return (
      <p className="rounded bg-amber-50 p-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">{error}</p>
    );
  if (!data) return <p className="text-sm text-slate-500">Loading eval summary (GET /evals/summary)…</p>;

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Evaluations</h1>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard label="Accuracy" value={`${(data.accuracy * 100).toFixed(1)}%`} />
        <KpiCard label="SQL validity" value={`${(data.sqlValidity * 100).toFixed(1)}%`} />
        <KpiCard label="Latency p95" value={`${data.latencyP95Ms} ms`} />
        <KpiCard label="Hallucination rate" value={`${(data.hallucinationRate * 100).toFixed(2)}%`} />
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-lg border p-4 dark:border-slate-800">
          <ChartRenderer
            chart={{
              kind: "line",
              title: "Accuracy over time",
              xKey: "date",
              yKey: "accuracy",
              data: data.series,
            }}
            height={260}
          />
        </div>
        <div className="rounded-lg border p-4 dark:border-slate-800">
          <ChartRenderer
            chart={{
              kind: "line",
              title: "Latency (ms) over time",
              xKey: "date",
              yKey: "latencyMs",
              data: data.series,
            }}
            height={260}
          />
        </div>
        <div className="rounded-lg border p-4 dark:border-slate-800">
          <ChartRenderer
            chart={{
              kind: "bar",
              title: "SQL validity over time",
              xKey: "date",
              yKey: "sqlValidity",
              data: data.series,
            }}
            height={260}
          />
        </div>
        <div className="rounded-lg border p-4 dark:border-slate-800">
          <ChartRenderer
            chart={{
              kind: "bar",
              title: "Hallucinations over time",
              xKey: "date",
              yKey: "hallucinations",
              data: data.series,
            }}
            height={260}
          />
        </div>
      </div>
      <p className="text-xs text-slate-500">p50 latency: {data.latencyP50Ms} ms</p>
    </div>
  );
}
