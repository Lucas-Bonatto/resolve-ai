import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EvaluationCenter } from "../src/features/evaluations/evaluation-center";
import { WarRoom } from "../src/features/war-room/war-room";
import { api } from "../src/lib/api";
import type { EvaluationRun, IncidentSnapshot, RuntimeCapabilities } from "../src/types/domain";

vi.mock("../src/lib/api", () => ({
  API_URL: "http://127.0.0.1:8000",
  api: {
    runtime: vi.fn(),
    incident: vi.fn(),
    injectFlagship: vi.fn(),
    decide: vi.fn(),
    evaluationRuns: vi.fn(),
    runEvals: vi.fn(),
  },
}));

const publicRuntime: RuntimeCapabilities = {
  deployment_profile: "public_showcase",
  interactive: false,
  mutations_allowed: false,
  real_ai_enabled: false,
  fictional_data: true,
};

const snapshot: IncidentSnapshot = {
  incident: {
    id: "INC-2026-0042",
    title: "Approved payments remain pending",
    description: "Fictional flagship incident",
    severity: "SEV-1",
    state: "AWAITING_APPROVAL",
    affected_service: "webhook-worker",
    affected_customers: 37,
    execution_status: "SIMULATED",
    correlation_id: "corr_public_test",
    created_at: "2026-10-06T00:00:00Z",
    updated_at: "2026-10-06T00:01:00Z",
  },
  events: [],
  evidence: [],
  hypotheses: [],
  diagnosis: null,
  remediation_plan: null,
  approval: {
    id: "approval_public_test",
    incident_id: "INC-2026-0042",
    tool_call_id: "tool_public_test",
    tool_name: "request_service_rollback",
    requested_action: "Rollback webhook worker",
    reason: "Evidence supports the parser regression.",
    evidence_ids: [],
    potential_impact: "Brief simulated interruption.",
    expires_at: "2026-10-06T01:00:00Z",
    approved_by: null,
    status: "PENDING",
    consumed_at: null,
    correlation_id: "corr_public_test",
    agent_run_id: null,
  },
  tool_calls: [],
  run: null,
  validation: null,
  report: null,
};

const evaluation: EvaluationRun = {
  id: "eval_public_test",
  provider: "demo",
  model: "deterministic-demo-v1",
  sample_data: false,
  suite_version: "resolveai-benchmark-v1",
  run_kind: "deterministic-contract",
  code_revision: "abc1234",
  created_at: "2026-10-06T00:00:00Z",
  metrics: { case_count: 0 },
  results: [],
};

describe("public showcase UI", () => {
  beforeEach(() => {
    vi.mocked(api.runtime).mockResolvedValue(publicRuntime);
    vi.mocked(api.incident).mockResolvedValue(snapshot);
    vi.mocked(api.evaluationRuns).mockResolvedValue([evaluation]);
  });

  it("keeps critical incident decisions visibly disabled", async () => {
    render(<WarRoom incidentId="INC-2026-0042" />);

    expect(await screen.findByRole("heading", { name: "Decisão necessária" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Rejeitar reversão" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Aprovar reversão exata" })).toBeDisabled();
    expect(screen.getByText("Vitrine pública somente leitura.")).toBeInTheDocument();
  });

  it("shows committed evaluation provenance without an execution control", async () => {
    render(<EvaluationCenter />);

    expect(await screen.findByRole("button", { name: "Execução desabilitada" })).toBeDisabled();
    expect(screen.getByText("Resultado versionado, modo somente leitura.")).toBeInTheDocument();
    expect(api.runEvals).not.toHaveBeenCalled();
  });
});
