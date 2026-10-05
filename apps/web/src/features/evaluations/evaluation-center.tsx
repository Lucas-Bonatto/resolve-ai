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

const timestamp = (value: string) => new Intl.DateTimeFormat("en", {
  dateStyle: "medium",
  timeStyle: "medium",
  timeZone: "UTC",
}).format(new Date(value));

const revision = (value: string) => value === "unknown" ? "Not configured" : value;

function passCount(run: EvaluationRun): number {
  return run.results.filter(result => result.passed).length;
}

export function EvaluationCenter() {
  const [runs, setRuns] = useState<EvaluationRun[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.evaluationRuns().then(setRuns).catch(() => undefined);
  }, []);

  const run = runs[0] ?? sample;
  const previous = runs[1] ?? null;
  const execute = async () => {
    setRunning(true); setError(null);
    try {
      const next = await api.runEvals();
      setRuns(current => [next, ...current.filter(item => item.id !== next.id)]);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Evaluation failed");
    } finally {
      setRunning(false);
    }
  };

  const failures = run.results.filter(result => !result.passed);
  const passed = passCount(run);
  const total = run.results.length;
  const probeCount = Number(run.metrics.critical_boundary_probe_count ?? 0);
  const averageDuration = Number(run.metrics.average_investigation_duration_ms ?? 0);
  const previousPassed = previous ? passCount(previous) : 0;
  const delta = previous ? passed - previousPassed : 0;
  const resultTone = run.sample_data ? "warning" : failures.length ? "warning" : "success";
  const scoreTone = failures.length ? "warn" : "good";
  const failureLabel = `${failures.length} ${failures.length === 1 ? "failure" : "failures"}`;
  const liveMessage = running
    ? "Evaluation running. 40 cases queued."
    : run.sample_data
      ? "No evaluation has executed in this process."
      : `Evaluation complete. ${passed} of ${total} cases passed. ${failureLabel}.`;

  return <>
    <div className="evaluation-topbar" aria-busy={running}>
      <div>
        <StatusBadge tone={resultTone}>{run.sample_data ? "Sample data" : "Executed result"}</StatusBadge>
        <p>{run.provider} · {run.model} · {run.metrics.case_count ?? total} cases</p>
      </div>
      <button className="button button-primary" disabled={running} onClick={execute}>
        <EvalIcon />{running ? "Running 40 cases…" : "Run evaluation"}
      </button>
    </div>
    <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{liveMessage}</p>
    {error && <div className="error-banner" role="alert">{error}. Start the API with <code>make dev-api</code>.</div>}
    <section className={`evaluation-summary ${run.sample_data ? "evaluation-summary-empty" : failures.length ? "evaluation-summary-warning" : "evaluation-summary-success"}`} aria-labelledby="evaluation-result-title">
      <div>
        <span className="priority-eyebrow">Deterministic evaluation contract</span>
        <h2 id="evaluation-result-title">{run.sample_data ? "No evaluation executed in this process" : `${passed} / ${total} cases passed`}</h2>
        <p>{run.sample_data ? "Run the suite to produce an auditable result from the current API process." : failures.length ? "The run completed with a visible regression. Security targets remain separate from scenario accuracy." : "The run completed without a visible contract regression."}</p>
      </div>
      <dl className="evaluation-provenance">
        <div><dt>Executed</dt><dd>{run.sample_data ? "Awaiting run" : `${timestamp(run.created_at)} UTC`}</dd></div>
        <div><dt>Code revision</dt><dd>{revision(run.code_revision)}</dd></div>
        <div><dt>Boundary probes</dt><dd>{run.sample_data ? "—" : probeCount}</dd></div>
        <div><dt>Average case duration</dt><dd>{run.sample_data ? "—" : `${averageDuration.toFixed(1)} ms`}</dd></div>
      </dl>
    </section>
    <section className="content-grid eval-metrics">
      <MetricCard label="Scenario contract success" value={run.sample_data ? "—" : percent(run.metrics.scenario_contract_success_rate)} detail="Passed cases / executed cases" tone={scoreTone} />
      <MetricCard label="Root-cause top-1" value={run.sample_data ? "—" : percent(run.metrics.root_cause_top_1_accuracy)} detail="Deterministic expected truth" tone={failures.length ? "warn" : "good"} />
      <MetricCard label="Evidence recall" value={run.sample_data ? "—" : percent(run.metrics.required_evidence_recall)} detail="Required IDs found" tone={(run.metrics.required_evidence_recall ?? 0) < 1 && !run.sample_data ? "warn" : "good"} />
      <MetricCard label="Evidence violations" value={run.sample_data ? "—" : String(run.metrics.evidence_integrity_violations ?? 0)} detail="Security target: 0" tone={(run.metrics.evidence_integrity_violations ?? 0) > 0 ? "warn" : "good"} />
      <MetricCard label="Prompt-injection bypass" value={run.sample_data ? "—" : String(run.metrics.prompt_injection_bypasses ?? 0)} detail={`${probeCount || "—"} active boundary probes · target 0`} tone={(run.metrics.prompt_injection_bypasses ?? 0) > 0 ? "warn" : "good"} />
      <MetricCard label="Unauthorized writes" value={run.sample_data ? "—" : String(run.metrics.unauthorized_critical_tool_execution ?? 0)} detail={`${probeCount || "—"} active boundary probes · target 0`} tone={(run.metrics.unauthorized_critical_tool_execution ?? 0) > 0 ? "warn" : "good"} />
    </section>
    <section className="content-grid dashboard-main">
      <article className="panel"><header className="panel-header"><h2>Benchmark coverage</h2><StatusBadge tone="info">Deterministic graders</StatusBadge></header><div className="bar-chart">{[
        ["Payments", 10], ["Reliability", 10], ["Database", 5], ["Auth + queue", 5], ["Security", 5], ["Insufficient", 5],
      ].map(([label, value]) => <div className="bar-column" key={label}><b>{value}</b><div className="bar" style={{ height: `${Number(value) * 12}px` }} /><span>{label}</span></div>)}</div></article>
      <article className="panel"><header className="panel-header"><h2>Run provenance</h2><StatusBadge tone="neutral">{run.sample_data ? "Not executed" : "Executed"}</StatusBadge></header><div className="panel-body summary-list"><div><span>Provider</span><b>{run.provider}</b></div><div><span>Model</span><b>{run.model}</b></div><div><span>Run kind</span><b>{run.run_kind}</b></div><div><span>Suite</span><b>{run.suite_version}</b></div><div><span>Code revision</span><b>{revision(run.code_revision)}</b></div><div><span>Executed at</span><b>{run.sample_data ? "Not executed" : `${timestamp(run.created_at)} UTC`}</b></div><div><span>Cases</span><b>{total}</b></div><div><span>Known regressions</span><b>{failures.length}</b></div><div><span>Result ID</span><b>{run.id}</b></div></div></article>
    </section>
    <article className="panel evaluation-comparison"><header className="panel-header"><h2>Previous-run comparison</h2><StatusBadge tone="neutral">In-process history</StatusBadge></header>{previous ? <div className="panel-body summary-list"><div><span>Previous result</span><b>{previousPassed} / {previous.results.length} passed</b></div><div><span>Pass-count delta</span><b>{delta > 0 ? `+${delta}` : delta} cases</b></div><div><span>Previous revision</span><b>{revision(previous.code_revision)}</b></div><div><span>Previous result ID</span><b>{previous.id}</b></div></div> : <div className="empty-state"><strong>No prior run in this process.</strong><p>Run the deterministic suite again to compare executed results. Demo reset intentionally clears this local history.</p></div>}</article>
    <article className="panel evaluation-failures"><header className="panel-header"><h2 id="failing-cases-title">Failing cases stay visible</h2><StatusBadge tone={run.sample_data ? "neutral" : failures.length ? "warning" : "success"}>{run.sample_data ? "Not executed" : failureLabel}</StatusBadge></header>{failures.length ? <div className="table-scroll" role="region" aria-labelledby="failing-cases-title" tabIndex={0}><table className="data-table"><caption className="sr-only">Failing evaluation cases</caption><thead><tr><th>Case</th><th>Result</th><th>Evidence recall</th><th>Failure reason</th></tr></thead><tbody>{failures.map(item => <tr key={item.case_id}><td><strong>{item.case_id}</strong></td><td><StatusBadge tone="critical">Failed</StatusBadge></td><td>{percent(item.evidence_recall)}</td><td>{item.failure_reason}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>{run.sample_data ? "No evaluation has run in this process." : "No failing cases in this run."}</strong><p>{run.sample_data ? "Run the deterministic suite to compute product and security metrics." : "Compare with the previous run before promoting a provider or prompt change."}</p></div>}</article>
  </>;
}
