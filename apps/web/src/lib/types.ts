// Shared domain types for InsightForge web client.
// Mirrors the API contracts owned by apps/api (that team owns the source of truth).

export type PiiType = "email" | "phone" | "name" | "address" | "ssn" | "other";

export interface PiiWarning {
  column: string;
  piiType: PiiType | string;
  count: number;
  sampleMasked?: string;
}

export interface Column {
  name: string;
  dtype: string;
  nullable: boolean;
  uniqueCount?: number | null;
  missingCount?: number | null;
  missingPct?: number | null;
  mean?: number | null;
  min?: number | string | null;
  max?: number | string | null;
  topValues?: Array<{ value: string | number; count: number }>;
  isPii?: boolean;
  piiType?: PiiType | string | null;
}

export interface QualityMetrics {
  completeness: number;
  validity: number;
  uniqueness: number;
  consistency: number;
  overall: number;
}

export interface Profile {
  rowCount: number;
  colCount: number;
  quality: QualityMetrics;
  missingByColumn: Array<{ column: string; missingCount: number; missingPct: number }>;
  distributions: Array<{
    column: string;
    kind: "histogram" | "categorical" | "numeric";
    bins?: Array<{ label: string; count: number }>;
  }>;
  piiWarnings: PiiWarning[];
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  rowCount: number;
  colCount: number;
  quality: QualityMetrics | number;
  piiWarnings?: PiiWarning[];
  createdAt: string;
  updatedAt?: string;
  owner?: string;
}

export interface DatasetDetail extends Dataset {
  schema: Column[];
  profile: Profile;
  sampleRows: Array<Record<string, string | number | boolean | null>>;
}

export interface Session {
  id: string;
  datasetId: string;
  title: string;
  createdAt: string;
}

export interface PlanStep {
  id: string;
  title: string;
  kind: string;
  detail?: string;
  status?: "pending" | "running" | "done" | "failed";
}

export interface Plan {
  steps: PlanStep[];
  reasoningSummary?: string;
  estimatedCost?: string;
}

export interface Query {
  sql: string;
  durationMs?: number;
  rowCount?: number;
  rows?: Array<Record<string, string | number | boolean | null>>;
  columns?: string[];
  intermediateResults?: Array<{ label: string; rowCount: number; durationMs?: number }>;
}

export type ChartKind =
  | "line"
  | "bar"
  | "stackedbar"
  | "scatter"
  | "histogram"
  | "box"
  | "area"
  | "pie"
  | "heatmap"
  | "table";

export interface Chart {
  kind: ChartKind;
  title?: string;
  xKey?: string;
  yKey?: string;
  seriesKeys?: string[];
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  data: Array<Record<string, any>>;
  config?: Record<string, string | number | boolean>;
}

export interface Evidence {
  id: string;
  kind: "row" | "query" | "doc" | "metric";
  label: string;
  detail?: string;
  rowIds?: string[];
  queryId?: string;
}

export interface Question {
  id: string;
  sessionId: string;
  question: string;
  answer: string;
  sql?: string;
  plan?: Plan;
  query?: Query;
  charts?: Chart[];
  evidence?: Evidence[];
  followUps?: string[];
  durationMs?: number;
  createdAt: string;
}

export interface Insight {
  id: string;
  title: string;
  body: string;
  datasetId?: string;
  questionId?: string;
  createdAt: string;
  tags?: string[];
}

export interface Report {
  id: string;
  title: string;
  summary: string;
  kpis: Array<{ label: string; value: string | number; delta?: string }>;
  charts: Chart[];
  findings: string[];
  evidence: Evidence[];
  risks: string[];
  nextQuestions: string[];
  createdAt: string;
}

export interface EvalSummary {
  accuracy: number;
  sqlValidity: number;
  latencyP50Ms: number;
  latencyP95Ms: number;
  hallucinationRate: number;
  series: Array<{ date: string; accuracy: number; sqlValidity: number; latencyMs: number; hallucinations: number }>;
}

export interface AuditEntry {
  id: string;
  actor: string;
  action: string;
  resource: string;
  createdAt: string;
  detail?: string;
}
