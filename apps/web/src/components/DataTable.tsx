interface Props {
  columns: string[];
  rows: Array<Record<string, string | number | boolean | null>>;
  maxHeight?: number;
}

function cell(v: string | number | boolean | null): string {
  if (v === null || v === undefined) return "—";
  return String(v);
}

export default function DataTable({ columns, rows, maxHeight = 420 }: Props) {
  if (rows.length === 0) return <p className="text-sm text-slate-500">No rows.</p>;
  return (
    <div
      className="overflow-auto rounded-lg border border-slate-200 dark:border-slate-800"
      style={{ maxHeight }}
    >
      <table className="min-w-full text-sm">
        <thead className="sticky top-0 bg-slate-50 dark:bg-slate-900">
          <tr>
            {columns.map((c) => (
              <th key={c} className="whitespace-nowrap px-3 py-2 text-left font-semibold">
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-slate-100 dark:border-slate-800">
              {columns.map((c) => (
                <td key={c} className="max-w-[240px] truncate px-3 py-1.5" title={cell(r[c])}>
                  {cell(r[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
