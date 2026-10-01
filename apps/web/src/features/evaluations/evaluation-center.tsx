"use client";

import { useEffect, useState } from "react";
import { EvalIcon } from "@/components/icons";
import { MetricCard, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import type { EvaluationRun } from "@/types/domain";

const sample: EvaluationRun = {
  id: "not-executed", provider: "demo", model: "deterministic-demo-v1", sample_data: true,
  suite_version: "resolveai-benchmark-v1", run_kind: "deterministic-contract", code_revision: "unknown",
  created_at: "2026-09-30T00:00:00Z", metrics: { case_count: 0 }, results: [],
};

const percent = (value = 0) => {
  const percentage = value * 100;
  return `${Number.isInteger(percentage) ? percentage : percentage.toFixed(1)}%`;
};

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
      <MetricCard label="Scenario contract success" value={run.sample_data ? "—" : percent(run.metrics.scenario_contract_success_rate)} detail="Passed cases / executed cases" tone="good" />
      <MetricCard label="Root-cause top-1" value={run.sample_data ? "—" : percent(run.metrics.root_cause_top_1_accuracy)} detail="Deterministic expected truth" tone="good" />
      <MetricCard label="Evidence recall" value={run.sample_data ? "—" : percent(run.metrics.required_evidence_recall)} detail="Required IDs found" tone="good" />
      <MetricCard label="Evidence violations" value={run.sample_data ? "—" : String(run.metrics.evidence_integrity_violations ?? 0)} detail="Security target: 0" />
      <MetricCard label="Prompt-injection bypass" value={run.sample_data ? "—" : String(run.metrics.prompt_injection_bypasses ?? 0)} detail="Security target: 0" tone="good" />
      <MetricCard label="Unauthorized writes" value={run.sample_data ? "—" : String(run.metrics.unauthorized_critical_tool_execution ?? 0)} detail="Security target: 0" tone="good" />
    </section>
    <section className="content-grid dashboard-main">
      <article className="panel"><header className="panel-header"><h2>Benchmark coverage</h2><StatusBadge tone="info">Deterministic graders</StatusBadge></header><div className="bar-chart">{[
        ["Payments", 10], ["Reliability", 10], ["Database", 5], ["Auth + queue", 5], ["Security", 5], ["Insufficient", 5],
      ].map(([label, value]) => <div className="bar-column" key={label}><b>{value}</b><div className="bar" style={{ height: `${Number(value) * 12}px` }} /><span>{label}</span></div>)}</div></article>
      <article className="panel"><header className="panel-header"><h2>Run contract</h2><StatusBadge tone="neutral">{run.sample_data ? "Not executed" : "Executed"}</StatusBadge></header><div className="panel-body summary-list"><div><span>Provider</span><b>{run.provider}</b></div><div><span>Model</span><b>{run.model}</b></div><div><span>Run kind</span><b>{run.run_kind}</b></div><div><span>Suite</span><b>{run.suite_version}</b></div><div><span>Code revision</span><b>{run.code_revision}</b></div><div><span>Cases</span><b>{run.results.length}</b></div><div><span>Known regressions</span><b>{failures.length}</b></div><div><span>Result ID</span><b>{run.id}</b></div></div></article>
    </section>
    <article className="panel" style={{ marginTop: 16 }}><header className="panel-header"><h2>Failing cases stay visible</h2><StatusBadge tone={run.sample_data ? "neutral" : failures.length ? "warning" : "success"}>{run.sample_data ? "Not executed" : `${failures.length} failures`}</StatusBadge></header>{failures.length ? <table className="data-table"><thead><tr><th>Case</th><th>Result</th><th>Evidence recall</th><th>Failure reason</th></tr></thead><tbody>{failures.map(item => <tr key={item.case_id}><td><strong>{item.case_id}</strong></td><td><StatusBadge tone="critical">Failed</StatusBadge></td><td>{percent(item.evidence_recall)}</td><td>{item.failure_reason}</td></tr>)}</tbody></table> : <div className="empty-state"><strong>{run.sample_data ? "No evaluation has run in this process." : "No failing cases in this run."}</strong><p>{run.sample_data ? "Run the deterministic suite to compute product and security metrics." : "Compare with the previous run before promoting a provider or prompt change."}</p></div>}</article>
  </>;
}
