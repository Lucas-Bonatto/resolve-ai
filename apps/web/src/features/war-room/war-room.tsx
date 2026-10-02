"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckIcon, IncidentIcon, SparkIcon } from "@/components/icons";
import { StatusBadge } from "@/components/ui";
import { API_URL, api } from "@/lib/api";
import type { Evidence, IncidentSnapshot } from "@/types/domain";

const terminalStates = new Set(["RESOLVED", "FAILED", "ESCALATED"]);

function tone(state: string): "success" | "critical" | "warning" | "info" | "neutral" {
  if (state === "RESOLVED" || state === "COMPLETED") return "success";
  if (state === "FAILED" || state === "SEV-1") return "critical";
  if (state === "AWAITING_APPROVAL" || state === "ESCALATED") return "warning";
  if (["INVESTIGATING", "DIAGNOSING", "EXECUTING", "VALIDATING"].includes(state)) return "info";
  return "neutral";
}

function time(value: string): string {
  return new Intl.DateTimeFormat("en", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date(value));
}

function confidenceLabel(value: number): "Low" | "Medium" | "High" {
  if (value >= 0.75) return "High";
  if (value >= 0.45) return "Medium";
  return "Low";
}

export function WarRoom({ incidentId }: { incidentId: string }) {
  const [snapshot, setSnapshot] = useState<IncidentSnapshot | null>(null);
  const [selected, setSelected] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const next = await api.incident(incidentId);
      setSnapshot(next);
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not refresh incident");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    let active = true;
    api.incident(incidentId)
      .then(next => { if (active) { setSnapshot(next); setError(null); } })
      .catch(() => undefined)
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [incidentId]);

  const incidentState = snapshot?.incident.state;
  const lastEventId = snapshot?.events.at(-1)?.id;
  useEffect(() => {
    if (!incidentState || terminalStates.has(incidentState)) return;
    const cursor = lastEventId ? `?after_id=${encodeURIComponent(lastEventId)}` : "";
    const events = new EventSource(`${API_URL}/api/incidents/${incidentId}/events/stream${cursor}`);
    events.addEventListener("incident", () => { void refresh(); });
    events.onerror = () => setError("Live stream interrupted. ResolveAI will reconnect automatically.");
    return () => events.close();
  }, [incidentId, incidentState, lastEventId, refresh]);

  const launch = async () => {
    setBusy(true); setError(null);
    try { await api.injectFlagship(); await refresh(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Could not launch the demo"); }
    finally { setBusy(false); setLoading(false); }
  };

  const decide = async (decision: "approve" | "reject") => {
    if (!snapshot?.approval) return;
    setBusy(true); setError(null);
    try { await api.decide(snapshot.approval.id, decision); await refresh(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Decision could not be recorded"); }
    finally { setBusy(false); }
  };

  const orderedEvents = useMemo(() => snapshot ? [...snapshot.events].reverse() : [], [snapshot]);

  if (loading) return <div className="launch-state"><div><div className="launch-orbit skeleton" /><div className="skeleton" style={{ height: 30, width: 270, margin: "0 auto 10px" }} /><div className="skeleton" style={{ height: 15, width: 390, maxWidth: "90%", margin: "0 auto" }} /></div></div>;
  if (!snapshot) return <div className="launch-state"><div><div className="launch-orbit"><IncidentIcon /></div><StatusBadge tone="critical">Flagship scenario · SEV-1</StatusBadge><h2>Payment Webhook Regression</h2><p>Inject a controlled incident, then watch ResolveAI collect evidence, test hypotheses, pause at a critical rollback, and validate the outcome.</p><button className="button button-primary" disabled={busy} onClick={launch}><SparkIcon /> {busy ? "Injecting…" : "Inject incident"}</button>{error && <div className="error-banner" role="alert">{error}<br />Start the API with <code>make dev-api</code>.</div>}</div></div>;

  return <>
    <section className="war-header"><div><p className="breadcrumb">{snapshot.incident.id} / Incident war room</p><h2>{snapshot.incident.title}</h2><p>{snapshot.incident.description}</p></div><div className="war-meta"><StatusBadge tone="critical">{snapshot.incident.severity}</StatusBadge><StatusBadge tone={tone(snapshot.incident.state)}>{snapshot.incident.state.replaceAll("_", " ")}</StatusBadge><StatusBadge tone="neutral">{snapshot.incident.execution_status}</StatusBadge></div></section>
    {error && <div className="error-banner" role="alert">{error}</div>}
    <div className="war-grid">
      <aside className="war-column">
        <section className="war-card"><header className="war-card-head"><h3>Incident summary</h3><StatusBadge tone="neutral">Live</StatusBadge></header><div className="war-card-body summary-list"><div><span>Affected service</span><b>{snapshot.incident.affected_service}</b></div><div><span>Customers</span><b>{snapshot.incident.affected_customers}</b></div><div><span>Evidence</span><b>{snapshot.evidence.length} records</b></div><div><span>Tool calls</span><b>{snapshot.tool_calls.length}</b></div><div><span>Provider</span><b>{snapshot.run?.provider ?? "Starting"}</b></div><div><span>Correlation ID</span><b>{snapshot.incident.correlation_id}</b></div><div><span>Trace ID</span>{snapshot.run ? <Link href={`/runs/${snapshot.run.id}`}><b>{snapshot.run.trace_id}</b></Link> : <b>—</b>}</div></div></section>
        <section className="war-card"><header className="war-card-head"><h3>Evidence locker</h3><span className="status-badge status-neutral">{snapshot.evidence.length}</span></header><div className="war-card-body evidence-grid">{snapshot.evidence.length ? snapshot.evidence.map(item => <button className="evidence-button" key={item.id} onClick={() => setSelected(item)} aria-label={`Inspect evidence ${item.id}`}><span className="evidence-type">{item.source_type.slice(0, 3)}</span><span><b>{item.id}</b><span>{item.title}</span></span><strong>{Math.round(item.relevance * 100)}%</strong></button>) : <div className="empty-state"><strong>No evidence collected yet.</strong><p>Evidence will appear when validated tool results enter the incident record.</p></div>}</div></section>
        {selected && <section className="war-card"><header className="war-card-head"><h3>{selected.id}</h3><button onClick={() => setSelected(null)}>Close</button></header><div className="war-card-body"><p style={{ fontSize: 11, lineHeight: 1.55, marginTop: 0 }}>{selected.summary}</p><pre style={{ overflow: "auto", fontSize: 9, background: "#f4f6f2", padding: 10, borderRadius: 8 }}>{JSON.stringify(selected.raw_payload, null, 2)}</pre></div></section>}
      </aside>

      <section className="war-column" aria-label="Investigation">
        <section className="war-card"><header className="war-card-head"><h3>Investigation timeline</h3><span className="status-badge status-info"><i className="live-dot" /> Event stream</span></header><div className="timeline">{orderedEvents.map(event => <article className={`timeline-event ${event.type.startsWith("tool") ? "tool" : event.type.startsWith("approval") ? "approval" : ""}`} key={event.id}><span className="timeline-time">{time(event.created_at)}</span><h4>{event.title}</h4><p>{event.summary}</p><div className="event-meta"><span>{event.type}</span><span>{event.status}</span>{typeof event.metadata.duration_ms === "number" && <span>{event.metadata.duration_ms} ms</span>}</div></article>)}</div></section>
        {snapshot.diagnosis && <section className="diagnosis-card"><small>Decision summary · {confidenceLabel(snapshot.diagnosis.confidence)} heuristic confidence · {snapshot.diagnosis.outcome.replaceAll("_", " ")}</small><h3>{snapshot.diagnosis.probable_root_cause}</h3><p>{snapshot.diagnosis.summary} {snapshot.diagnosis.recommended_next_step}</p><div className="evidence-pills">{snapshot.diagnosis.evidence_ids.map(id => <span key={id}>{id}</span>)}</div></section>}
        {snapshot.remediation_plan && <section className="war-card"><header className="war-card-head"><h3>Remediation plan</h3><StatusBadge tone="critical">Critical</StatusBadge></header><div className="war-card-body"><p style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.55 }}>{snapshot.remediation_plan.summary}</p>{snapshot.remediation_plan.steps.map((step, index) => <div className="service-row" key={step.id}><span><b>{index + 1}. {step.title}</b><br /><small>{step.description}</small></span><StatusBadge tone={step.status === "SIMULATED" ? "success" : step.risk_level === "critical_write" ? "critical" : "neutral"}>{step.status}</StatusBadge></div>)}</div></section>}
        {snapshot.validation && <section className="war-card"><header className="war-card-head"><h3>Post-remediation validation</h3><StatusBadge tone={snapshot.validation.passed ? "success" : "critical"}>{snapshot.validation.passed ? "Verified" : "Failed"}</StatusBadge></header><div className="war-card-body summary-list"><div><span>Summary</span><b>{snapshot.validation.summary}</b></div><div><span>Checks</span><b>{snapshot.validation.checks_passed} passed · {snapshot.validation.checks_failed} failed</b></div><div><span>Transactions recovered</span><b>{snapshot.validation.recovered_transactions}</b></div></div></section>}
        {snapshot.report && <section className="war-card"><header className="war-card-head"><h3>Incident report</h3><StatusBadge tone={tone(snapshot.report.final_status)}>{snapshot.report.final_status}</StatusBadge></header><div className="war-card-body"><p style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.55 }}>{snapshot.report.summary}</p><div className="summary-list"><div><span>Evidence references</span><b>{snapshot.report.evidence_ids.length}</b></div><div><span>Hypotheses considered</span><b>{snapshot.report.hypothesis_ids.length}</b></div><div><span>Correlation ID</span><b>{snapshot.report.correlation_id}</b></div></div></div></section>}
      </section>

      <aside className="war-column">
        <section className="war-card"><header className="war-card-head"><h3>Hypothesis engine</h3><span className="status-badge status-neutral">{snapshot.hypotheses.length}</span></header><div className="war-card-body">{snapshot.hypotheses.length ? snapshot.hypotheses.map(item => <article className="hypothesis" key={item.id}><div className="hypothesis-head"><h4>{item.title}</h4><small>{confidenceLabel(item.confidence)} · {item.status}</small></div><div className="confidence-bar"><span style={{ width: `${item.confidence * 100}%` }} /></div><p>{item.description}</p><small>Verify: {item.verification_strategy}</small>{(item.evidence_for.length > 0 || item.evidence_against.length > 0) && <div className="evidence-pills" aria-label={`Evidence for ${item.title}`}>{item.evidence_for.map(id => <span key={`for-${id}`}>Supports {id}</span>)}{item.evidence_against.map(id => <span key={`against-${id}`}>Contradicts {id}</span>)}</div>}</article>) : <div className="empty-state"><strong>Hypotheses are forming.</strong><p>ResolveAI does not jump directly to a root cause.</p></div>}</div></section>
        {snapshot.approval?.status === "PENDING" ? <section className="war-card approval-live"><header className="war-card-head"><h3>Decision required</h3><StatusBadge tone="critical">Critical write</StatusBadge></header><div className="war-card-body approval-detail"><div><label>Requested action</label><p><b>{snapshot.approval.requested_action}</b></p></div><div><label>Why</label><p>{snapshot.approval.reason}</p></div><div><label>Potential impact</label><p>{snapshot.approval.potential_impact}</p></div><div><label>Evidence</label><div className="evidence-pills">{snapshot.approval.evidence_ids.map(id => <span key={id}>{id}</span>)}</div></div><div className="approval-buttons"><button className="button button-danger" disabled={busy} onClick={() => decide("reject")}>Reject</button><button className="button button-success" disabled={busy} onClick={() => decide("approve")}><CheckIcon />Approve</button></div></div></section> : <section className="war-card"><header className="war-card-head"><h3>Human approvals</h3></header><div className="empty-state"><strong>{snapshot.approval ? `Decision: ${snapshot.approval.status}` : "No decision waiting on you."}</strong><p>{snapshot.approval ? `Recorded for ${snapshot.approval.requested_action}.` : "ResolveAI has no critical action pending approval."}</p></div></section>}
        <section className="war-card"><header className="war-card-head"><h3>Permission boundary</h3><StatusBadge tone="success">Enforced</StatusBadge></header><div className="war-card-body summary-list"><div><span>Read tools</span><b>Automatic</b></div><div><span>Safe writes</span><b>Audited</b></div><div><span>Critical writes</span><b>Approval</b></div><div><span>Policy owner</span><b>Backend</b></div></div></section>
      </aside>
    </div>
  </>;
}
