"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { listDatasets, uploadDataset, getApiErrorMessage } from "@/lib/api";
import type { Dataset } from "@/lib/types";
import UploadDropzone from "@/components/UploadDropzone";

function qualityPct(d: Dataset): string {
  const q = typeof d.quality === "number" ? d.quality : d.quality.overall;
  return `${(q * 100).toFixed(1)}%`;
}

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      setDatasets(await listDatasets());
    } catch (e) {
      setError(getApiErrorMessage(e));
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function onFile(file: File) {
    setUploading(true);
    setError(null);
    try {
      await uploadDataset(file);
      await refresh();
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Datasets</h1>
        <button
          onClick={() => void refresh()}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          Refresh
        </button>
      </div>

      <UploadDropzone onFile={(f) => void onFile(f)} busy={uploading} />

      {loading && <p className="text-sm text-slate-500">Loading datasets…</p>}
      {error && (
        <p className="rounded bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">
          {error}
        </p>
      )}
      {!loading && !error && datasets.length === 0 && (
        <p className="rounded border border-dashed p-6 text-center text-sm text-slate-500">
          No datasets yet. Upload a CSV above — it calls POST /datasets/upload.
        </p>
      )}

      {datasets.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800">
          <table className="min-w-full text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900">
              <tr>
                <th className="px-4 py-2 text-left">Name</th>
                <th className="px-4 py-2 text-right">Rows</th>
                <th className="px-4 py-2 text-right">Cols</th>
                <th className="px-4 py-2 text-right">Quality</th>
                <th className="px-4 py-2 text-left">PII warnings</th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.id} className="border-t border-slate-200 dark:border-slate-800">
                  <td className="px-4 py-2">
                    <Link href={`/datasets/${d.id}`} className="font-medium text-blue-600 hover:underline">
                      {d.name}
                    </Link>
                    {d.description && (
                      <div className="text-xs text-slate-500">{d.description}</div>
                    )}
                  </td>
                  <td className="px-4 py-2 text-right">{d.rowCount.toLocaleString()}</td>
                  <td className="px-4 py-2 text-right">{d.colCount}</td>
                  <td className="px-4 py-2 text-right">{qualityPct(d)}</td>
                  <td className="px-4 py-2">
                    {(d.piiWarnings?.length ?? 0) === 0 ? (
                      <span className="text-slate-400">none</span>
                    ) : (
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-xs text-amber-900 dark:bg-amber-900 dark:text-amber-100">
                        {d.piiWarnings!.length} warning(s)
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
