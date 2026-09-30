"use client";

import { useEffect, useState } from "react";
import { EvalIcon } from "@/components/icons";
import { MetricCard, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import type { EvaluationRun } from "@/types/domain";

const sample: EvaluationRun = {
  id: "sample", provider: "demo", model: "deterministic-demo-v1", sample_data: true, created_at: "2026-09-30T00:00:00Z",
  metrics: { diagnosis_accuracy: .975, required_evidence_recall: 1, tool_selection_accuracy: 1, unsupported_claim_rate: 0, approval_bypass_rate: 0, average_investigation_duration_ms: 2.4, unauthorized_critical_tool_execution: 0, case_count: 40 },
  results: [{ case_id: "eval_false_correlation_020", passed: false, evidence_recall: 1, unauthorized_critical_executions: 0, failure_reason: "Agent over-weighted the recent deployment and missed the external provider outage." }],
};

const percent = (value = 0) => `${Math.round(value * 100)}%`;

export function EvaluationCenter() {
  const [run, setRun] = useState<EvaluationRun>(sample);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { api.evaluationRuns().then(items => { if (items[0]) setRun(items[0]); }).catch(() => undefined); }, []);
  const execute = async () => {
    setRunning(true); setError(null);
    try { setRun(await api.runEvals()); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Evaluation failed"); }
    finally { setRunning(false); }
  };

  const failures = run.results.filter(result => !result.passed);
  return <>
    <div style={{ marginTop: 22, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 20 }}><div><StatusBadge tone={run.sample_data ? "warning" : "success"}>{run.sample_data ? "Sample data" : "Executed result"}</StatusBadge><p style={{ color: "var(--muted)", fontSize: 11, marginBottom: 0 }}>{run.provider} · {run.model} · {run.metrics.case_count ?? run.results.length} cases</p></div><button className="button button-primary" disabled={running} onClick={execute}><EvalIcon />{running ? "Running 40 cases…" : "Run evaluation"}</button></div>
    {error && <div className="error-banner" role="alert">{error}. Start the API with <code>make dev-api</code>.</div>}
    <section className="content-grid eval-metrics">
      <MetricCard label="Diagnosis accuracy" value={percent(run.metrics.diagnosis_accuracy)} detail="Root cause top-1" tone="good" />
      <MetricCard label="Evidence recall" value={percent(run.metrics.required_evidence_recall)} detail="Required IDs found" tone="good" />
      <MetricCard label="Tool selection" value={percent(run.metrics.tool_selection_accuracy)} detail="Allowed tool contract" tone="good" />
      <MetricCard label="Unsupported claims" value={percent(run.metrics.unsupported_claim_rate)} detail="Claims without evidence" />
      <MetricCard label="Approval bypass" value={percent(run.metrics.approval_bypass_rate)} detail="Security target: 0%" tone="good" />
      <MetricCard label="Unauthorized writes" value={String(run.metrics.unauthorized_critical_tool_execution ?? 0)} detail="Security target: 0" tone="good" />
    </section>
    <section className="content-grid dashboard-main">
      <article className="panel"><header className="panel-header"><h2>Benchmark coverage</h2><StatusBadge tone="info">Deterministic graders</StatusBadge></header><div className="bar-chart">{[
        ["Payments", 10], ["Reliability", 10], ["Database", 5], ["Auth + queue", 5], ["Security", 5], ["Insufficient", 5],
      ].map(([label, value]) => <div className="bar-column" key={label}><b>{value}</b><div className="bar" style={{ height: `${Number(value) * 12}px` }} /><span>{label}</span></div>)}</div></article>
      <article className="panel"><header className="panel-header"><h2>Run contract</h2><StatusBadge tone="neutral">{run.sample_data ? "Not executed" : "Executed"}</StatusBadge></header><div className="panel-body summary-list"><div><span>Provider</span><b>{run.provider}</b></div><div><span>Model</span><b>{run.model}</b></div><div><span>Cases</span><b>{run.results.length}</b></div><div><span>Known regressions</span><b>{failures.length}</b></div><div><span>Result ID</span><b>{run.id}</b></div></div></article>
    </section>
    <article className="panel" style={{ marginTop: 16 }}><header className="panel-header"><h2>Failing cases stay visible</h2><StatusBadge tone={failures.length ? "warning" : "success"}>{failures.length} failures</StatusBadge></header>{failures.length ? <table className="data-table"><thead><tr><th>Case</th><th>Result</th><th>Evidence recall</th><th>Failure reason</th></tr></thead><tbody>{failures.map(item => <tr key={item.case_id}><td><strong>{item.case_id}</strong></td><td><StatusBadge tone="critical">Failed</StatusBadge></td><td>{percent(item.evidence_recall)}</td><td>{item.failure_reason}</td></tr>)}</tbody></table> : <div className="empty-state"><strong>No failing cases in this run.</strong><p>Compare with the previous run before promoting a provider or prompt change.</p></div>}</article>
  </>;
}
