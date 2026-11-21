"use client";

import { useEffect, useState } from "react";
import { generateReport, getReport, listReports, getApiErrorMessage } from "@/lib/api";
import type { Report } from "@/lib/types";
import ChartRenderer from "@/components/ChartRenderer";
import EvidencePanel from "@/components/EvidencePanel";

function toMarkdown(r: Report): string {
  const lines = [
    `# ${r.title}`,
    ``,
    `## Summary`,
    r.summary,
    ``,
    `## KPIs`,
    ...r.kpis.map((k) => `- ${k.label}: ${k.value}${k.delta ? ` (${k.delta})` : ""}`),
    ``,
    `## Findings`,
    ...r.findings.map((f) => `- ${f}`),
    ``,
    `## Risks`,
    ...r.risks.map((x) => `- ${x}`),
    ``,
    `## Next questions`,
    ...r.nextQuestions.map((q) => `- ${q}`),
    ``,
    `## Evidence`,
    ...r.evidence.map((e) => `- [${e.kind}] ${e.label}`),
  ];
  return lines.join("\n");
}

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [current, setCurrent] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("Q3 Executive Summary");

  async function refresh() {
    try {
      const items = await listReports();
      setReports(items);
      if (items[0] && !current) setCurrent(await getReport(items[0].id));
      setError(null);
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onGenerate() {
    setError(null);
    try {
      const r = await generateReport({ title });
      setReports((p) => [r, ...p]);
      setCurrent(r);
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  }

  function onExportMd() {
    if (!current) return;
    const blob = new Blob([toMarkdown(current)], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${current.title.replace(/\s+/g, "-").toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="text-xl font-bold">Executive Reports</h1>
        <div className="ml-auto flex gap-2">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="rounded-md border px-2 py-1.5 text-sm dark:border-slate-700 dark:bg-slate-900"
            placeholder="Report title"
          />
          <button onClick={() => void onGenerate()} className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-blue-700">
            Generate (POST /reports)
          </button>
          <button onClick={() => window.print()} className="rounded-md border px-3 py-1.5 text-sm hover:bg-slate-50 dark:border-slate-700">
            Print
          </button>
          <button onClick={onExportMd} disabled={!current} className="rounded-md border px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700">
            Export .md
          </button>
        </div>
      </div>

      {error && <p className="rounded bg-amber-50 p-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">{error}</p>}

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-1 rounded-lg border p-3 dark:border-slate-800">
          {reports.map((r) => (
            <button
              key={r.id}
              onClick={() => void getReport(r.id).then(setCurrent).catch((e) => setError(getApiErrorMessage(e)))}
              className={`w-full rounded px-2 py-1.5 text-left text-sm hover:bg-slate-50 dark:hover:bg-slate-800 ${current?.id === r.id ? "bg-slate-100 dark:bg-slate-800" : ""}`}
            >
              {r.title}
            </button>
          ))}
          {reports.length === 0 && <p className="text-sm text-slate-500">No reports yet.</p>}
        </aside>

        <article className="space-y-4 rounded-lg border p-5 dark:border-slate-800">
          {!current ? (
            <p className="text-sm text-slate-500">Generate or select a report.</p>
          ) : (
            <>
              <div>
                <h2 className="text-lg font-bold">{current.title}</h2>
                <p className="mt-1 text-sm">{current.summary}</p>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {current.kpis.map((k) => (
                  <div key={k.label} className="rounded border p-2.5 dark:border-slate-700">
                    <div className="text-xs text-slate-500">{k.label}</div>
                    <div className="font-bold">{k.value}</div>
                    {k.delta && <div className="text-xs text-green-600">{k.delta}</div>}
                  </div>
                ))}
              </div>
              {current.charts.map((c, i) => (
                <ChartRenderer key={i} chart={c} height={260} />
              ))}
              <section>
                <h3 className="font-semibold">Findings</h3>
                <ul className="list-disc pl-5 text-sm">{current.findings.map((f, i) => <li key={i}>{f}</li>)}</ul>
              </section>
              <section>
                <h3 className="font-semibold">Evidence</h3>
                <EvidencePanel evidence={current.evidence} />
              </section>
              <section>
                <h3 className="font-semibold">Risks</h3>
                <ul className="list-disc pl-5 text-sm">{current.risks.map((f, i) => <li key={i}>{f}</li>)}</ul>
              </section>
              <section>
                <h3 className="font-semibold">Next questions</h3>
                <ul className="list-disc pl-5 text-sm">{current.nextQuestions.map((f, i) => <li key={i}>{f}</li>)}</ul>
              </section>
            </>
          )}
        </article>
      </div>
    </div>
  );
}
