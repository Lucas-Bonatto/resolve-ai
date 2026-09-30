"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import type { AgentRun } from "@/types/domain";

export function RunDetail({ runId }: { runId: string }) {
  const [run, setRun] = useState<AgentRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.run(runId).then(setRun).catch((cause: unknown) => {
      setError(cause instanceof Error ? cause.message : "Run unavailable");
    });
  }, [runId]);

  if (error) return <div className="error-banner" role="alert">{error}. The API returned no fabricated fallback.</div>;
  if (!run) return <div className="empty-state"><strong>Loading run…</strong><p>Retrieving the recorded execution contract.</p></div>;

  const complete = run.status === "COMPLETED";
  return <>
    <div style={{ marginTop: 22 }}><StatusBadge tone={complete ? "success" : run.status === "FAILED" ? "critical" : "info"}>{run.status}</StatusBadge></div>
    <section className="content-grid metrics-grid">
      <article className="metric-card"><span>Tool calls</span><strong>{run.tool_call_count}</strong><small>Bounded by application policy</small></article>
      <article className="metric-card"><span>Input tokens</span><strong>{run.input_tokens ?? "—"}</strong><small>Unavailable in deterministic mode</small></article>
      <article className="metric-card"><span>Output tokens</span><strong>{run.output_tokens ?? "—"}</strong><small>Unavailable in deterministic mode</small></article>
      <article className="metric-card"><span>Estimated cost</span><strong>{run.estimated_cost_usd == null ? "$—" : `$${run.estimated_cost_usd.toFixed(4)}`}</strong><small>No synthetic estimate</small></article>
    </section>
    <article className="panel" style={{ marginTop: 16 }}>
      <header className="panel-header"><h2>Execution record</h2><StatusBadge tone="neutral">{run.provider}</StatusBadge></header>
      <div className="panel-body summary-list">
        <div><span>Run ID</span><b>{run.id}</b></div>
        <div><span>Trace ID</span><b>{run.trace_id}</b></div>
        <div><span>Workflow</span><b>{run.workflow}</b></div>
        <div><span>Model</span><b>{run.model}</b></div>
        <div><span>Started</span><b>{new Date(run.started_at).toLocaleString()}</b></div>
        <div><span>Completed</span><b>{run.completed_at ? new Date(run.completed_at).toLocaleString() : "In progress"}</b></div>
        <div><span>Incident</span><Link href={`/incidents/${run.incident_id}`}><b>{run.incident_id}</b></Link></div>
        <div><span>Error</span><b>{run.error ?? "None recorded"}</b></div>
      </div>
    </article>
  </>;
}
