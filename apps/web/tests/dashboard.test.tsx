import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { DashboardOverview } from "../src/features/dashboard/dashboard-overview";
import { api } from "../src/lib/api";
import type { EvaluationRun, Incident } from "../src/types/domain";

vi.mock("../src/lib/api", () => ({
  api: {
    incidents: vi.fn(),
    evaluationRuns: vi.fn(),
  },
}));

const incident: Incident = {
  id: "INC-2026-0042",
  title: "Approved payments remain pending",
  description: "Fictional flagship incident",
  severity: "SEV-1",
  state: "RESOLVED",
  affected_service: "webhook-worker",
  affected_customers: 37,
  execution_status: "SIMULATED",
  correlation_id: "corr_test",
  created_at: "2026-10-02T10:00:00Z",
  updated_at: "2026-10-02T10:05:00Z",
};

const run: EvaluationRun = {
  id: "eval_test",
  provider: "demo",
  model: "deterministic-demo-v1",
  sample_data: false,
  suite_version: "resolveai-benchmark-v1",
  run_kind: "deterministic-contract",
  code_revision: "abc1234",
  created_at: "2026-10-02T10:06:00Z",
  metrics: {
    critical_boundary_probe_count: 2,
    prompt_injection_bypasses: 0,
    unauthorized_critical_tool_execution: 0,
  },
  results: [
    { case_id: "pass", passed: true, failure_reason: null, evidence_recall: 1, unauthorized_critical_executions: 0, prompt_injection_bypasses: 0, evidence_integrity_violations: 0, structured_output_valid: true, tool_failure_handled: true },
    { case_id: "known-regression", passed: false, failure_reason: "Expected mismatch", evidence_recall: 1, unauthorized_critical_executions: 0, prompt_injection_bypasses: 0, evidence_integrity_violations: 0, structured_output_valid: true, tool_failure_handled: true },
  ],
};

describe("dashboard overview", () => {
  beforeEach(() => {
    vi.mocked(api.incidents).mockResolvedValue([incident]);
    vi.mocked(api.evaluationRuns).mockResolvedValue([run]);
  });

  it("renders backend truth separately from labeled fixture sections", async () => {
    render(<DashboardOverview />);

    expect(await screen.findByText("1/2")).toBeInTheDocument();
    expect(screen.getByText("Resolvido", { exact: true })).toBeInTheDocument();
    expect(screen.getByText("2 sondagens ativas de limite")).toBeInTheDocument();
    expect(screen.getByText("Histórico de exemplo")).toBeInTheDocument();
    expect(screen.getByText("Dados de exemplo")).toBeInTheDocument();
    expect(screen.queryByText("Aguardando demonstração")).not.toBeInTheDocument();
  });

  it("keeps incident truth visible when only evaluation data is unavailable", async () => {
    vi.mocked(api.evaluationRuns).mockRejectedValue(new Error("Evaluation offline"));

    render(<DashboardOverview />);

    expect(await screen.findByText("Resolvido", { exact: true })).toBeInTheDocument();
    expect(screen.getAllByText("Falha na API de avaliações", { exact: true })).toHaveLength(2);
    expect(screen.getByText("Não foi possível verificar o resultado")).toBeInTheDocument();
    expect(screen.queryByText("Não executada", { exact: true })).not.toBeInTheDocument();
  });
});
