export type IncidentState =
  | "NEW" | "TRIAGED" | "INVESTIGATING" | "EVIDENCE_COLLECTED" | "DIAGNOSING"
  | "DIAGNOSED" | "PLAN_PROPOSED" | "AWAITING_APPROVAL" | "EXECUTING"
  | "VALIDATING" | "RESOLVED" | "FAILED" | "ESCALATED";

export type RiskLevel = "read" | "safe_write" | "critical_write";
export type ExecutionStatus = "EXECUTED" | "SIMULATED" | "NOT_EXECUTED" | "BLOCKED";

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: "SEV-1" | "SEV-2" | "SEV-3";
  state: IncidentState;
  affected_service: string;
  affected_customers: number;
  execution_status: ExecutionStatus;
  correlation_id: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentEvent {
  id: string;
  incident_id: string;
  type: string;
  title: string;
  summary: string;
  status: ExecutionStatus;
  created_at: string;
  metadata: Record<string, unknown>;
  correlation_id: string;
  agent_run_id: string | null;
  tool_call_id: string | null;
  approval_id: string | null;
}

export interface Evidence {
  id: string;
  incident_id: string;
  source_type: string;
  source_reference: string;
  title: string;
  summary: string;
  raw_payload: Record<string, unknown>;
  created_at: string;
  relevance: number;
  correlation_id: string;
}

export interface Hypothesis {
  id: string;
  title: string;
  description: string;
  confidence: number;
  evidence_for: string[];
  evidence_against: string[];
  verification_strategy: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Diagnosis {
  outcome: "SUPPORTED_ROOT_CAUSE" | "INSUFFICIENT_EVIDENCE";
  summary: string;
  probable_root_cause: string;
  confidence: number;
  evidence_ids: string[];
  affected_services: string[];
  recommended_next_step: string;
}

export interface RemediationStep {
  id: string;
  title: string;
  description: string;
  tool_name: string | null;
  arguments: Record<string, unknown>;
  risk_level: RiskLevel;
  status: ExecutionStatus;
}

export interface RemediationPlan {
  id: string;
  summary: string;
  steps: RemediationStep[];
  risk_level: RiskLevel;
  rollback_plan: string | null;
  validation_plan: string;
}

export interface Approval {
  id: string;
  incident_id: string;
  tool_call_id: string;
  tool_name: string;
  requested_action: string;
  reason: string;
  evidence_ids: string[];
  potential_impact: string;
  expires_at: string;
  approved_by: string | null;
  status: "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED" | "CONSUMED";
  consumed_at: string | null;
  correlation_id: string;
  agent_run_id: string | null;
}

export interface ToolCall {
  id: string;
  incident_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  risk_level: RiskLevel;
  status: ExecutionStatus;
  evidence_ids: string[];
  duration_ms: number | null;
  output_summary: string | null;
  created_at: string;
  correlation_id: string;
  agent_run_id: string | null;
}

export interface AgentRun {
  id: string;
  incident_id: string;
  provider: string;
  model: string;
  workflow: string;
  status: string;
  trace_id: string;
  correlation_id: string;
  started_at: string;
  completed_at: string | null;
  tool_call_count: number;
  input_tokens: number | null;
  output_tokens: number | null;
  estimated_cost_usd: number | null;
  error: string | null;
}

export interface ValidationResult {
  incident_id: string;
  passed: boolean;
  summary: string;
  evidence_ids: string[];
  checks_passed: number;
  checks_failed: number;
  recovered_transactions: number;
  created_at: string;
}

export interface IncidentReport {
  incident_id: string;
  correlation_id: string;
  summary: string;
  timeline_event_ids: string[];
  evidence_ids: string[];
  hypothesis_ids: string[];
  diagnosis: Diagnosis | null;
  remediation_plan_id: string | null;
  approval_id: string | null;
  validation: ValidationResult | null;
  final_status: IncidentState;
  generated_at: string;
}

export interface IncidentSnapshot {
  incident: Incident;
  events: IncidentEvent[];
  evidence: Evidence[];
  hypotheses: Hypothesis[];
  diagnosis: Diagnosis | null;
  remediation_plan: RemediationPlan | null;
  approval: Approval | null;
  tool_calls: ToolCall[];
  run: AgentRun | null;
  validation: ValidationResult | null;
  report: IncidentReport | null;
}

export interface EvaluationRun {
  id: string;
  provider: string;
  model: string;
  sample_data: boolean;
  suite_version: string;
  run_kind: string;
  code_revision: string;
  created_at: string;
  metrics: Record<string, number>;
  results: Array<{
    case_id: string;
    passed: boolean;
    failure_reason: string | null;
    evidence_recall: number;
    unauthorized_critical_executions: number;
    prompt_injection_bypasses: number;
    evidence_integrity_violations: number;
    structured_output_valid: boolean;
    tool_failure_handled: boolean;
  }>;
}
