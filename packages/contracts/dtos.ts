/**
 * InsightForge shared DTOs (lightweight contracts).
 * Owned by the data+evals+docs slice. Backend/frontend slices must conform.
 */

export type DatasetName = "ecommerce" | "saas" | "cloud_spend" | "manufacturing";

export interface ProfileColumn {
  name: string;
  dtype: string;
  nullRate: number;
  distinctCount: number;
  min?: string | number | null;
  max?: string | number | null;
  mean?: number | null;
  isPII: boolean;
}

export interface DatasetProfile {
  dataset: DatasetName;
  rows: number;
  columns: ProfileColumn[];
  dateRange: { min: string; max: string } | null;
  warnings: string[];
}

export interface EvidenceBundle {
  dataset: string;
  filters: string[];
  rowSample: string[];
  sql: string;
}

export interface AskRequest {
  question: string;
  dataset: DatasetName | "auto";
  maxRows?: number;
}

export interface AskResponse {
  answer: string;
  sql: string;
  rows: Record<string, unknown>[];
  chartSpec: ChartSpec | null;
  evidence: EvidenceBundle;
  latencyMs: number;
  tokensUsed: number;
  warnings: string[];
}

export type ChartKind = "bar" | "line" | "scatter" | "table";

export interface ChartSpec {
  kind: ChartKind;
  x: string;
  y: string;
  title: string;
}

export interface EvalQuestion {
  id: string;
  category:
    | "simple_lookup" | "aggregation" | "multi_step" | "time_comparison"
    | "root_cause" | "correlation" | "outlier" | "ambiguous"
    | "unanswerable" | "security";
  question: string;
  dataset: DatasetName | "ecommerce";
  expected_sql_contains: string[];
  expected_answer: string;
  notes: string;
}
