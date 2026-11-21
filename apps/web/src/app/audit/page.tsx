"use client";

import { useEffect, useState } from "react";
import { listAudit, getApiErrorMessage } from "@/lib/api";
import type { AuditEntry } from "@/lib/types";

export default function AuditPage() {
  const [rows, setRows] = useState<AuditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    setLoading(true);
    try {
      setRows(await listAudit(100));
      setError(null);
    } catch (e) {
      setError(getApiErrorMessage(e));
      setRows([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Audit log</h1>
        <button
          onClick={() => void refresh()}
          className="rounded-md border px-3 py-1.5 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          Refresh (GET /audit)
        </button>
      </div>
      {loading && <p className="text-sm text-slate-500">Loading…</p>}
      {error && <p className="rounded bg-amber-50 p-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">{error}</p>}
      {!loading && !error && rows.length === 0 && (
        <p className="rounded border border-dashed p-6 text-center text-sm text-slate-500">No audit entries.</p>
      )}
      {rows.length > 0 && (
        <div className="overflow-x-auto rounded-lg border dark:border-slate-800">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900">
              <tr>
                <th className="px-3 py-2 text-left">Time</th>
                <th className="px-3 py-2 text-left">Actor</th>
                <th className="px-3 py-2 text-left">Action</th>
                <th className="px-3 py-2 text-left">Resource</th>
                <th className="px-3 py-2 text-left">Detail</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t dark:border-slate-800">
                  <td className="whitespace-nowrap px-3 py-1.5">{new Date(r.createdAt).toLocaleString()}</td>
                  <td className="px-3 py-1.5">{r.actor}</td>
                  <td className="px-3 py-1.5 font-mono text-xs">{r.action}</td>
                  <td className="px-3 py-1.5 font-mono text-xs">{r.resource}</td>
                  <td className="px-3 py-1.5 text-xs text-slate-500">{r.detail ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
