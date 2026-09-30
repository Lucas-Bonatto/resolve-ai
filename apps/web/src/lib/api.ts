import type { AgentRun, EvaluationRun, IncidentSnapshot } from "@/types/domain";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: init?.body ? { "content-type": "application/json", ...init.headers } : init?.headers,
    cache: "no-store",
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ message: response.statusText }));
    throw new Error(payload.message ?? payload.detail ?? "Request failed");
  }
  return response.json() as Promise<T>;
}

export const api = {
  injectFlagship: () => request<{ incident: { id: string }; status: string }>("/api/chaos/scenarios/payment-webhook-regression/inject", { method: "POST" }),
  incident: (id: string) => request<IncidentSnapshot>(`/api/incidents/${id}`),
  decide: (approvalId: string, decision: "approve" | "reject") => request(`/api/approvals/${approvalId}/${decision}`, { method: "POST", body: JSON.stringify({ actor: "demo-operator" }) }),
  runEvals: () => request<EvaluationRun>("/api/evals/run", { method: "POST" }),
  evaluationRuns: () => request<EvaluationRun[]>("/api/evals/runs"),
  audit: () => request<Array<Record<string, unknown>>>("/api/audit"),
  run: (id: string) => request<AgentRun>(`/api/runs/${id}`),
};
