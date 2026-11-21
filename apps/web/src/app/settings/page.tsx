"use client";

import { useState } from "react";
import { api, getApiErrorMessage } from "@/lib/api";

export default function SettingsPage() {
  const [retention, setRetention] = useState("90");
  const [masking, setMasking] = useState(true);
  const [role, setRole] = useState("analyst");
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  async function onSave() {
    setMsg(null);
    setErr(null);
    try {
      // Real API call: backend owns /settings (falls back gracefully if unimplemented).
      await api.put("/settings", {
        retentionDays: Number(retention),
        piiMasking: masking,
        defaultRole: role,
      });
      setMsg("Settings saved (PUT /settings).");
    } catch (e) {
      setErr(getApiErrorMessage(e));
    }
  }

  return (
    <div className="max-w-xl space-y-4">
      <h1 className="text-xl font-bold">Settings</h1>
      <label className="block text-sm">
        Data retention (days)
        <input
          value={retention}
          onChange={(e) => setRetention(e.target.value)}
          inputMode="numeric"
          className="mt-1 w-full rounded-md border px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
        />
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={masking} onChange={(e) => setMasking(e.target.checked)} />
        Mask PII in samples and evidence
      </label>
      <label className="block text-sm">
        Default role
        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="mt-1 w-full rounded-md border px-3 py-2 dark:border-slate-700 dark:bg-slate-900"
        >
          <option value="viewer">viewer</option>
          <option value="analyst">analyst</option>
          <option value="admin">admin</option>
        </select>
      </label>
      <button
        onClick={() => void onSave()}
        className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
      >
        Save settings
      </button>
      {msg && <p className="rounded bg-green-50 p-2 text-sm text-green-700 dark:bg-green-950 dark:text-green-200">{msg}</p>}
      {err && <p className="rounded bg-amber-50 p-2 text-sm text-amber-800 dark:bg-amber-950 dark:text-amber-200">{err}</p>}
    </div>
  );
}
