import axios from "axios";
import type {
  AuditEntry,
  Dataset,
  DatasetDetail,
  EvalSummary,
  Insight,
  Question,
  Report,
  Session,
} from "./types";

const baseURL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export const api = axios.create({ baseURL, timeout: 30000 });

const TOKEN_KEY = "insightforge_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

export function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as { detail?: string; message?: string } | undefined;
    if (data?.detail) return data.detail;
    if (data?.message) return data.message;
    if (err.code === "ECONNREFUSED" || err.message?.includes("Network Error"))
      return "API unreachable. Is the backend running at " + baseURL + "?";
    return err.message || "Request failed";
  }
  if (err instanceof Error) return err.message;
  return "Unknown error";
}

// --- Auth ---
export async function login(email: string, password: string): Promise<{ token: string }> {
  const { data } = await api.post("/auth/login", { email, password });
  if (data?.token) setToken(data.token);
  return data;
}

export async function me(): Promise<{ email: string; role: string }> {
  const { data } = await api.get("/auth/me");
  return data;
}

// --- Datasets ---
export async function listDatasets(): Promise<Dataset[]> {
  const { data } = await api.get("/datasets");
  return Array.isArray(data) ? data : data?.items ?? [];
}

export async function getDataset(id: string): Promise<DatasetDetail> {
  const { data } = await api.get(`/datasets/${id}`);
  return data;
}

export async function uploadDataset(file: File): Promise<Dataset> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/datasets/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// --- Sessions / Questions (analysis) ---
export async function listSessions(datasetId?: string): Promise<Session[]> {
  const { data } = await api.get("/sessions", { params: datasetId ? { datasetId } : {} });
  return Array.isArray(data) ? data : data?.items ?? [];
}

export async function createSession(datasetId: string, title: string): Promise<Session> {
  const { data } = await api.post("/sessions", { datasetId, title });
  return data;
}

export async function askQuestion(sessionId: string, question: string): Promise<Question> {
  const { data } = await api.post("/questions", { sessionId, question });
  return data;
}

export async function listQuestions(sessionId: string): Promise<Question[]> {
  const { data } = await api.get("/questions", { params: { sessionId } });
  return Array.isArray(data) ? data : data?.items ?? [];
}

// --- Insights ---
export async function listInsights(): Promise<Insight[]> {
  const { data } = await api.get("/insights");
  return Array.isArray(data) ? data : data?.items ?? [];
}

export async function saveInsight(payload: {
  title: string;
  body: string;
  datasetId?: string;
  questionId?: string;
}): Promise<Insight> {
  const { data } = await api.post("/insights", payload);
  return data;
}

export async function deleteInsight(id: string): Promise<void> {
  await api.delete(`/insights/${id}`);
}

// --- Reports ---
export async function listReports(): Promise<Report[]> {
  const { data } = await api.get("/reports");
  return Array.isArray(data) ? data : data?.items ?? [];
}

export async function getReport(id: string): Promise<Report> {
  const { data } = await api.get(`/reports/${id}`);
  return data;
}

export async function generateReport(payload: {
  title: string;
  datasetId?: string;
  sessionId?: string;
}): Promise<Report> {
  const { data } = await api.post("/reports", payload);
  return data;
}

// --- Evals ---
export async function getEvalSummary(): Promise<EvalSummary> {
  const { data } = await api.get("/evals/summary");
  return data;
}

// --- Audit ---
export async function listAudit(limit = 100): Promise<AuditEntry[]> {
  const { data } = await api.get("/audit", { params: { limit } });
  return Array.isArray(data) ? data : data?.items ?? [];
}

// --- Health ---
export async function healthz(): Promise<{ status: string }> {
  const { data } = await api.get("/healthz");
  return data;
}
