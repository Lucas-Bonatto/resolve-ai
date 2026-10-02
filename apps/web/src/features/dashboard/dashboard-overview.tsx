"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowIcon } from "@/components/icons";
import { MetricCard, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { services } from "@/lib/demo-data";
import type { EvaluationRun, Incident, IncidentState } from "@/types/domain";

const terminalStates = new Set<IncidentState>(["RESOLVED", "FAILED", "ESCALATED"]);

function label(value: string): string {
  return value.toLowerCase().replaceAll("_", " ").replace(/^./, character => character.toUpperCase());
}

function incidentTone(state: IncidentState): "neutral" | "critical" | "warning" | "success" | "info" {
  if (state === "RESOLVED") return "success";
  if (state === "FAILED") return "critical";
  if (state === "AWAITING_APPROVAL" || state === "ESCALATED") return "warning";
  if (state === "NEW") return "neutral";
  return "info";
}

function DashboardLoading() {
  return <>
    <section className="content-grid metrics-grid" aria-label="Loading live operational metrics">
      {[0, 1, 2, 3].map(item => <article className="metric-card" key={item}><div className="skeleton" style={{ height: 12, width: "62%" }} /><div className="skeleton" style={{ height: 34, width: "48%", marginTop: "auto" }} /></article>)}
    </section>
    <div className="dashboard-loading panel"><div className="skeleton" /><span>Loading live demo state…</span></div>
  </>;
}

export function DashboardOverview() {
  const [incidents, setIncidents] = useState<Incident[] | null>(null);
  const [latestRun, setLatestRun] = useState<EvaluationRun | null | undefined>(undefined);
  const [incidentError, setIncidentError] = useState<string | null>(null);
  const [evaluationError, setEvaluationError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.allSettled([api.incidents(), api.evaluationRuns()])
      .then(([incidentResult, evaluationResult]) => {
        if (!active) return;
        setIncidents(incidentResult.status === "fulfilled" ? incidentResult.value : []);
        setLatestRun(evaluationResult.status === "fulfilled" ? evaluationResult.value[0] ?? null : null);
        setIncidentError(incidentResult.status === "rejected" ? incidentResult.reason instanceof Error ? incidentResult.reason.message : "Incident request failed" : null);
        setEvaluationError(evaluationResult.status === "rejected" ? evaluationResult.reason instanceof Error ? evaluationResult.reason.message : "Evaluation request failed" : null);
      });
    return () => { active = false; };
  }, []);

  if (incidents === null || latestRun === undefined) return <DashboardLoading />;

  const openIncidents = incidents.filter(incident => !terminalStates.has(incident.state));
  const resolvedIncidents = incidents.filter(incident => incident.state === "RESOLVED");
  const failures = latestRun?.results.filter(result => !result.passed).length ?? 0;
  const passed = latestRun ? latestRun.results.length - failures : 0;
  const probes = latestRun?.metrics.critical_boundary_probe_count ?? 0;
  const criticalViolations = latestRun
    ? (latestRun.metrics.prompt_injection_bypasses ?? 0) + (latestRun.metrics.unauthorized_critical_tool_execution ?? 0)
    : null;
  const errors = [incidentError && `Incidents: ${incidentError}`, evaluationError && `Evaluation: ${evaluationError}`].filter(Boolean).join("; ");

  return <>
    {errors && <div className="error-banner" role="alert">Some live data is unavailable: {errors}. Fixture-only sections remain labeled below.</div>}
    <section className="content-grid metrics-grid" aria-label="Live operational metrics">
      <MetricCard label="Open incidents" value={incidentError ? "Unavailable" : String(openIncidents.length)} detail={incidentError ? "Incident API request failed" : "Current demo process"} tone={!incidentError && openIncidents.length ? "warn" : !incidentError ? "good" : "default"} />
      <MetricCard label="Resolved this session" value={incidentError ? "Unavailable" : String(resolvedIncidents.length)} detail={incidentError ? "Incident API request failed" : "Validated terminal incidents"} tone={!incidentError && resolvedIncidents.length ? "good" : "default"} />
      <MetricCard label="Latest evaluation" value={evaluationError ? "Unavailable" : latestRun ? `${passed}/${latestRun.results.length}` : "Not run"} detail={evaluationError ? "Evaluation API request failed" : latestRun ? `${failures} visible ${failures === 1 ? "failure" : "failures"}` : "No executed result in this process"} tone={!evaluationError && failures ? "warn" : !evaluationError && latestRun ? "good" : "default"} />
      <MetricCard label="Critical-policy violations" value={evaluationError ? "Unavailable" : criticalViolations === null ? "Not measured" : String(criticalViolations)} detail={evaluationError ? "Evaluation API request failed" : latestRun ? `${probes} active boundary probes` : "Run Evaluation Center to measure"} tone={!evaluationError && criticalViolations === 0 ? "good" : !evaluationError && criticalViolations ? "warn" : "default"} />
    </section>

    <section className="content-grid dashboard-main">
      <div className="stack">
        <article className="panel"><header className="panel-header"><h2>Live incident queue</h2><Link href="/incidents">View all <ArrowIcon /></Link></header>
          {incidents.length ? incidents.map(incident => <Link href={`/incidents/${incident.id}`} className="incident-row" key={incident.id}><div><h3>{incident.title}</h3><p>{incident.id} · {incident.affected_service} · {incident.affected_customers} affected</p></div><StatusBadge tone={incidentTone(incident.state)}>{incident.severity}</StatusBadge><div>{label(incident.state)}<br /><small>{incident.execution_status}</small></div></Link>) : <div className="empty-state"><strong>{incidentError ? "Live incident state is unavailable." : "No incident has been injected in this process."}</strong><p>{incidentError ? "Start the API to restore the live operational view." : "Open the flagship scenario to begin the deterministic workflow."}</p></div>}
        </article>
        <article className="panel"><header className="panel-header"><h2>Recent agent activity</h2><StatusBadge tone="neutral">Sample fixture history</StatusBadge></header><div className="panel-body activity-list">
          <div className="activity-item"><b>INC-2026-0038 · Resolution validated</b><p>Authentication key rotation completed after operator approval.</p></div>
          <div className="activity-item"><b>INC-2026-0031 · Evidence collected</b><p>Queue depth, consumer lag, and deployment window correlated.</p></div>
          <div className="activity-item"><b>Evaluation run · 40 cases</b><p>One known false-correlation regression remains visible for review.</p></div>
        </div></article>
      </div>
      <div className="stack">
        <article className="panel"><header className="panel-header"><h2>Service health</h2><StatusBadge tone="neutral">Sample fixture</StatusBadge></header><div className="panel-body">{services.map(service => <div className="service-row" key={service.name}><span><i className={`health-dot ${service.status === "Degraded" ? "degraded" : ""}`} />{service.name}</span><small>{service.latency}</small></div>)}</div></article>
        <article className="panel"><header className="panel-header"><h2>Evaluation posture</h2><Link href="/evals">Open center</Link></header><div className="panel-body"><div className="diagnosis-card"><small>{evaluationError ? "Evaluation unavailable" : latestRun ? "Executed deterministic result" : "Not executed in this process"}</small><h3>{evaluationError ? "Result status could not be verified" : latestRun ? `${passed} of ${latestRun.results.length} cases passed` : "Run before claiming results"}</h3><p>{evaluationError ? "The evaluation API request failed; no benchmark claim is shown." : latestRun ? `${failures} known ${failures === 1 ? "regression remains" : "regressions remain"} visible. Code revision: ${latestRun.code_revision}.` : "The Evaluation Center computes scenario results and actively probes the critical policy gateway."}</p><div className="evidence-pills"><span>{evaluationError ? "UNAVAILABLE" : latestRun ? `${latestRun.results.length} CASES` : "NOT EXECUTED"}</span><span>{evaluationError ? "NO CLAIM" : latestRun ? `${probes} BOUNDARY PROBES` : "NO MEASUREMENT"}</span><span>{evaluationError ? "RETRY REQUIRED" : latestRun ? `${failures} ${failures === 1 ? "FAILURE" : "FAILURES"}` : "RUN REQUIRED"}</span></div></div></div></article>
      </div>
    </section>
  </>;
}
