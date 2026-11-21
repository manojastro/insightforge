"use client";

import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  ScatterChart,
  Scatter,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import type { Chart } from "@/lib/types";
import DataTable from "./DataTable";

const COLORS = ["#2563eb", "#16a34a", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4"];

interface Props {
  chart: Chart;
  height?: number;
}

export default function ChartRenderer({ chart, height = 300 }: Props) {
  const { kind, title, xKey = "x", yKey = "y", seriesKeys = [], data } = chart;

  if (!data || data.length === 0) {
    return (
      <div>
        {title && <h3 className="mb-2 font-semibold">{title}</h3>}
        <p className="text-sm text-slate-500">No chart data.</p>
      </div>
    );
  }

  const series = seriesKeys.length > 0 ? seriesKeys : [yKey];

  function body() {
    switch (kind) {
      case "line":
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Line key={s} type="monotone" dataKey={s} stroke={COLORS[i % COLORS.length]} dot={false} />
            ))}
          </LineChart>
        );
      case "area":
        return (
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Area key={s} type="monotone" dataKey={s} fill={COLORS[i % COLORS.length]} stroke={COLORS[i % COLORS.length]} fillOpacity={0.3} />
            ))}
          </AreaChart>
        );
      case "bar":
      case "histogram":
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Bar key={s} dataKey={s} fill={COLORS[i % COLORS.length]} />
            ))}
          </BarChart>
        );
      case "stackedbar":
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Bar key={s} dataKey={s} stackId="a" fill={COLORS[i % COLORS.length]} />
            ))}
          </BarChart>
        );
      case "scatter":
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis dataKey={yKey} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Scatter data={data} fill={COLORS[0]} />
          </ScatterChart>
        );
      case "pie":
        return (
          <PieChart>
            <Tooltip />
            <Legend />
            <Pie data={data} dataKey={yKey} nameKey={xKey} outerRadius={100} label>
              {data.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
          </PieChart>
        );
      case "box": {
        // Approximate box display as bar of y values (full box-plot needs stats precomputed).
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={xKey} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey={yKey} fill={COLORS[4]} />
          </BarChart>
        );
      }
      case "heatmap": {
        // Render heatmap as a table of values (x rows, series columns).
        const cols = [xKey, ...series];
        return <DataTable columns={cols} rows={data.slice(0, 50)} maxHeight={300} />;
      }
      case "table": {
        const cols = Object.keys(data[0]);
        return <DataTable columns={cols} rows={data.slice(0, 100)} maxHeight={320} />;
      }
      default:
        return <p className="text-sm text-slate-500">Unsupported chart kind: {kind}</p>;
    }
  }

  return (
    <div>
      {title && <h3 className="mb-2 text-sm font-semibold">{title} <span className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-500 dark:bg-slate-800">{kind}</span></h3>}
      {kind === "heatmap" || kind === "table" ? (
        body()
      ) : (
        <ResponsiveContainer width="100%" height={height}>
          {body() as React.ReactElement}
        </ResponsiveContainer>
      )}
    </div>
  );
}
