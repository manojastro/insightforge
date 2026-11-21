"use client";

import { useEffect, useState } from "react";
import { deleteInsight, listInsights, getApiErrorMessage } from "@/lib/api";
import type { Insight } from "@/lib/types";

export default function InsightsPage() {
  const [items, setItems] = useState<Insight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setItems(await listInsights());
      setError(null);
    } catch (e) {
      setError(getApiErrorMessage(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onDelete(id: string) {
    try {
      await deleteInsight(id);
      await refresh();
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Saved Insights</h1>
        <button
          onClick={() => void refresh()}
          className="rounded-md border px-3 py-1.5 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          Refresh (GET /insights)
        </button>
      </div>
      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="rounded bg-amber-50 p-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="rounded border border-dashed p-6 text-center text-sm text-slate-500">
          No saved insights. Ask a question in Analysis, then click Save insight.
        </p>
      )}
      <div className="grid gap-3">
        {items.map((ins) => (
          <article key={ins.id} className="rounded-lg border p-4 dark:border-slate-800">
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-semibold">{ins.title}</h2>
              <button
                onClick={() => void onDelete(ins.id)}
                className="rounded border px-2 py-1 text-xs hover:bg-red-50 dark:border-slate-700 dark:hover:bg-red-950"
              >
                Delete
              </button>
            </div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-slate-600 dark:text-slate-300">{ins.body}</p>
            <div className="mt-2 text-xs text-slate-400">
              {new Date(ins.createdAt).toLocaleString()}
              {ins.tags?.length ? ` · ${ins.tags.join(", ")}` : ""}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
