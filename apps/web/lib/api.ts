"use strict";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000/api/v1";

export type ApiError = { detail?: string; status?: number };

class ApiErrorClass extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail || "Request failed");
    this.status = status;
    this.detail = detail || "Request failed";
    this.name = "ApiError";
  }
}

async function request(
  input: RequestInfo | URL,
  init: RequestInit = {}
): Promise<Response> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string> | undefined),
  };
  const res = await fetch(String(input), {
    ...init,
    headers,
    credentials: "include", // send HttpOnly session cookie
  });
  return res;
}

async function json<T>(res: Response): Promise<T> {
  const text = await res.text();
  if (!res.ok) {
    let detail = text || res.statusText;
    try {
      const parsed = JSON.parse(text);
      detail = parsed.detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiErrorClass(res.status, String(detail));
  }
  if (!text) return undefined as unknown as T;
  try {
    return JSON.parse(text);
  } catch {
    return undefined as unknown as T;
  }
}

export const api = {
  get: async <T>(path: string, init?: RequestInit) =>
    json<T>(await request(`${API_BASE}${path}`, { ...init, method: "GET" })),
  post: async <T>(path: string, body?: unknown, init?: RequestInit) =>
    json<T>(
      await request(`${API_BASE}${path}`, {
        ...init,
        method: "POST",
        body: body ? JSON.stringify(body) : undefined,
      })
    ),
  delete: async <T>(path: string, init?: RequestInit) =>
    json<T>(await request(`${API_BASE}${path}`, { ...init, method: "DELETE" })),
};

export { ApiErrorClass };

export async function authLogin(email: string, password: string) {
  const res = await request(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new ApiErrorClass(res.status, text || "Login failed");
  }
  return res.json();
}

export async function authLogout() {
  await request(`${API_BASE}/auth/logout`, { method: "POST" });
}

export async function authMe() {
  return api.get<{ id: string; email: string; username: string; roles: string[] }>("/auth/me");
}

export type Incident = {
  id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  source_type: string;
  source_ref: string | null;
  trace_id: string | null;
  repository_id: string | null;
  workflow_run_id: string | null;
  created_at: string;
  updated_at: string;
};

export type DashboardSummary = {
  active_incidents: number;
  critical_errors: number;
  failed_workflows: number;
  recent_repair_attempts: number;
  pending_approvals: number;
  verification_rate: string;
  integrations: Array<{ name: string; status: string }>;
};

export async function listIncidents() {
  return api.get<Incident[]>("/incidents");
}

export async function getDashboardSummary() {
  return api.get<DashboardSummary>("/dashboard/summary");
}

export async function getOllamaStatus() {
  return api.get<{ reachable: boolean; model_available: boolean; model: string; error: string | null; mode: string }>(
    "/system/ollama-status"
  );
}

export type Repository = {
  id: string;
  name: string;
  full_name: string;
  owner: string;
  default_branch: string;
  html_url: string | null;
  clone_url: string | null;
  allow_write: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export async function listRepositories() {
  return api.get<Repository[]>("/repositories");
}

export type ApprovalRequest = {
  id: string;
  resource: string;
  action_type: string;
  impact_summary: string;
  risk_classification: string;
  status: string;
  created_at: string;
  expires_at: string;
  patch_sha256: string | null;
  base_commit_sha: string | null;
  parameters: string;
  approver_id: string | null;
};

export async function listApprovals() {
  return api.get<ApprovalRequest[]>("/approvals");
}

export async function approveAction(id: string, reason?: string) {
  return api.post(`/approvals/${id}/approve`, { reason });
}

export async function rejectAction(id: string, reason?: string) {
  return api.post(`/approvals/${id}/reject`, { reason });
}

export async function revokeAction(id: string, reason?: string) {
  return api.post(`/approvals/${id}/revoke`, { reason });
}

export type AuditEvent = {
  event_id: string;
  action: string;
  resource: string;
  decision: string;
  result: string;
  actor_role: string | null;
  created_at: string;
};

export async function listAuditEvents() {
  return api.get<AuditEvent[]>("/audit-events");
}

export type WorkflowRun = {
  id: string;
  run_id: string;
  name: string;
  branch: string;
  sha: string;
  status: string;
  conclusion: string | null;
  url: string | null;
  started_at: string | null;
  completed_at: string | null;
  retry_count: number;
};

export async function listWorkflowRuns(repositoryId: string) {
  return api.get<WorkflowRun[]>(`/repositories/${repositoryId}/workflows`);
}
