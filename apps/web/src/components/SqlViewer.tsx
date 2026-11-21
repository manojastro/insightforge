"use client";

import { useState } from "react";

export default function SqlViewer({ sql }: { sql: string }) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(sql);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div className="rounded-lg border dark:border-slate-800">
      <div className="flex items-center justify-between border-b px-3 py-2 dark:border-slate-800">
        <span className="text-xs font-semibold uppercase text-slate-500">SQL</span>
        <button
          onClick={() => void onCopy()}
          className="rounded border px-2 py-1 text-xs hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <pre className="overflow-x-auto bg-slate-950 p-3 text-xs text-green-200">{sql}</pre>
    </div>
  );
}
