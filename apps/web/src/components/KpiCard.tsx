interface Props {
  label: string;
  value: string;
  delta?: string;
}

export default function KpiCard({ label, value, delta }: Props) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-bold">{value}</div>
      {delta && <div className="mt-1 text-xs text-green-600">{delta}</div>}
    </div>
  );
}
