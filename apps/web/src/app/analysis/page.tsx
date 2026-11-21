"use client";

import { useEffect, useState } from "react";
import {
  askQuestion,
  createSession,
  listDatasets,
  listQuestions,
  listSessions,
  saveInsight,
  getApiErrorMessage,
} from "@/lib/api";
import type { Dataset, Question, Session } from "@/lib/types";
import ChartRenderer from "@/components/ChartRenderer";
import DataTable from "@/components/DataTable";
import SqlViewer from "@/components/SqlViewer";
import PlanViewer from "@/components/PlanViewer";
import EvidencePanel from "@/components/EvidencePanel";

type Tab = "answer" | "charts" | "data" | "sql" | "plan" | "evidence";

export default function AnalysisPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [datasetId, setDatasetId] = useState("");
  const [sessions, setSessions] = useState<Session[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [history, setHistory] = useState<Question[]>([]);
  const [current, setCurrent] = useState<Question | null>(null);
  const [input, setInput] = useState("What are the top trends in this dataset?");
  const [tab, setTab] = useState<Tab>("answer");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const ds = await listDatasets();
        setDatasets(ds);
        if (ds[0]) setDatasetId(ds[0].id);
      } catch (e) {
        setError(getApiErrorMessage(e));
      }
    })();
  }, []);

  useEffect(() => {
    if (!datasetId) return;
    (async () => {
      try {
        const s = await listSessions(datasetId);
        setSessions(s);
        if (s[0]) setSessionId(s[0].id);
      } catch (e) {
        setError(getApiErrorMessage(e));
      }
    })();
  }, [datasetId]);

  useEffect(() => {
    if (!sessionId) return;
    (async () => {
      try {
        const q = await listQuestions(sessionId);
        setHistory(q);
        if (q[0]) setCurrent(q[0]);
      } catch {
        setHistory([]);
      }
    })();
  }, [sessionId]);

  async function ensureSession(): Promise<string> {
    if (sessionId) return sessionId;
    if (!datasetId) throw new Error("Select a dataset first.");
    const s = await createSession(datasetId, input.slice(0, 60) || "Untitled");
    setSessions((p) => [s, ...p]);
    setSessionId(s.id);
    return s.id;
  }

  async function onAsk(followUp?: string) {
    const q = (followUp ?? input).trim();
    if (!q) return;
    setLoading(true);
    setError(null);
    setNotice(null);
    try {
      const sid = await ensureSession();
      const ans = await askQuestion(sid, q);
      setHistory((p) => [ans, ...p]);
      setCurrent(ans);
      setTab("answer");
    } catch (e) {
      setError(getApiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }

  async function onSaveInsight() {
    if (!current) return;
    try {
      await saveInsight({
        title: current.question.slice(0, 80),
        body: current.answer,
        datasetId: datasetId || undefined,
        questionId: current.id,
      });
      setNotice("Saved to Insights (POST /insights).");
    } catch (e) {
      setError(getApiErrorMessage(e));
    }
  }

  const tabs: Array<{ id: Tab; label: string }> = [
    { id: "answer", label: "Answer" },
    { id: "charts", label: "Charts" },
    { id: "data", label: "Data" },
    { id: "sql", label: "SQL" },
    { id: "plan", label: "Plan" },
    { id: "evidence", label: "Evidence" },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[380px_1fr]">
      {/* Left: conversation */}
      <section className="space-y-3 rounded-lg border p-4 dark:border-slate-800">
        <h1 className="font-bold">Analysis</h1>
        <label className="block text-xs font-medium text-slate-500">
          Dataset
          <select
            value={datasetId}
            onChange={(e) => setDatasetId(e.target.value)}
            className="mt-1 w-full rounded-md border px-2 py-1.5 dark:border-slate-700 dark:bg-slate-900"
          >
            {datasets.map((d) => (
              <option key={d.id} value={d.id}>
                {d.name}
              </option>
            ))}
            {datasets.length === 0 && <option value="">No datasets</option>}
          </select>
        </label>
        <label className="block text-xs font-medium text-slate-500">
          Session
          <select
            value={sessionId}
            onChange={(e) => {
              setSessionId(e.target.value);
              const q = history.find((h) => h.sessionId === e.target.value);
              setCurrent(q ?? null);
            }}
            className="mt-1 w-full rounded-md border px-2 py-1.5 dark:border-slate-700 dark:bg-slate-900"
          >
            {sessions.map((s) => (
              <option key={s.id} value={s.id}>
                {s.title}
              </option>
            ))}
            {sessions.length === 0 && <option value="">New session on ask</option>}
          </select>
        </label>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={4}
          className="w-full rounded-md border px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-900"
          placeholder="Ask a question about the dataset…"
        />
        <button
          onClick={() => void onAsk()}
          disabled={loading}
          className="w-full rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Running…" : "Ask (POST /questions)"}
        </button>
        {error && <p className="rounded bg-red-50 p-2 text-xs text-red-700 dark:bg-red-950 dark:text-red-200">{error}</p>}
        {notice && <p className="rounded bg-green-50 p-2 text-xs text-green-700 dark:bg-green-950 dark:text-green-200">{notice}</p>}

        {current?.followUps && current.followUps.length > 0 && (
          <div>
            <h3 className="text-xs font-semibold uppercase text-slate-500">Follow-ups</h3>
            <div className="mt-1 flex flex-wrap gap-1.5">
              {current.followUps.map((f) => (
                <button
                  key={f}
                  onClick={() => {
                    setInput(f);
                    void onAsk(f);
                  }}
                  className="rounded-full border px-2.5 py-1 text-xs hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        )}

        <div>
          <h3 className="text-xs font-semibold uppercase text-slate-500">History (GET /questions)</h3>
          <ul className="mt-1 max-h-64 space-y-1 overflow-auto">
            {history.map((h) => (
              <li key={h.id}>
                <button
                  onClick={() => setCurrent(h)}
                  className={`w-full rounded border px-2 py-1.5 text-left text-xs hover:bg-slate-50 dark:hover:bg-slate-800 ${
                    current?.id === h.id ? "border-blue-500" : "dark:border-slate-700"
                  }`}
                >
                  {h.question}
                </button>
              </li>
            ))}
            {history.length === 0 && <li className="text-xs text-slate-500">No questions yet.</li>}
          </ul>
        </div>
      </section>

      {/* Right: tabs */}
      <section className="rounded-lg border dark:border-slate-800">
        <div className="flex flex-wrap gap-1 border-b p-2 dark:border-slate-800">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`rounded px-3 py-1.5 text-sm font-medium ${
                tab === t.id ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900" : "hover:bg-slate-100 dark:hover:bg-slate-800"
              }`}
            >
              {t.label}
            </button>
          ))}
          <button
            onClick={() => void onSaveInsight()}
            disabled={!current}
            className="ml-auto rounded border px-3 py-1.5 text-sm hover:bg-slate-50 disabled:opacity-50 dark:border-slate-700 dark:hover:bg-slate-800"
          >
            Save insight
          </button>
        </div>

        <div className="p-4">
          {!current ? (
            <p className="text-sm text-slate-500">Ask a question to see the answer, charts, SQL, plan, and evidence.</p>
          ) : (
            <>
              {tab === "answer" && (
                <div className="space-y-3">
                  <h2 className="font-semibold">{current.question}</h2>
                  <p className="whitespace-pre-wrap text-sm">{current.answer}</p>
                  <div className="rounded border p-3 text-xs text-slate-500 dark:border-slate-700">
                    Show My Work — plan: {current.plan?.steps.length ?? 0} steps · SQL:{" "}
                    {current.sql ? "yes" : "no"} · duration: {current.durationMs ?? current.query?.durationMs ?? "—"} ms ·
                    rows: {current.query?.rowCount ?? "—"} · chart: {current.charts?.[0]?.kind ?? "none"}
                    {current.plan?.reasoningSummary && <div className="mt-1">Reasoning: {current.plan.reasoningSummary}</div>}
                  </div>
                </div>
              )}
              {tab === "charts" &&
                (current.charts && current.charts.length > 0 ? (
                  <div className="grid gap-4">
                    {current.charts.map((c, i) => (
                      <ChartRenderer key={i} chart={c} height={300} />
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500">No charts returned.</p>
                ))}
              {tab === "data" &&
                (current.query?.rows && current.query.rows.length > 0 ? (
                  <DataTable columns={current.query.columns ?? Object.keys(current.query.rows[0])} rows={current.query.rows} />
                ) : (
                  <p className="text-sm text-slate-500">No data rows.</p>
                ))}
              {tab === "sql" && <SqlViewer sql={current.sql ?? current.query?.sql ?? "-- no SQL"} />}
              {tab === "plan" && (
                <PlanViewer
                  plan={current.plan}
                  meta={{
                    durationMs: current.durationMs ?? current.query?.durationMs,
                    rowCount: current.query?.rowCount,
                    intermediate: current.query?.intermediateResults,
                    chartConfig: current.charts?.[0]?.config,
                  }}
                />
              )}
              {tab === "evidence" && <EvidencePanel evidence={current.evidence ?? []} />}
            </>
          )}
        </div>
      </section>
    </div>
  );
}
