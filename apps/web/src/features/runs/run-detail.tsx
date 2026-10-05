"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatPtDate, statusLabel } from "@/lib/locale";
import type { AgentRun } from "@/types/domain";

export function RunDetail({ runId }: { runId: string }) {
  const [run, setRun] = useState<AgentRun | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.run(runId).then(setRun).catch((cause: unknown) => {
      setError(cause instanceof Error ? cause.message : "Execução indisponível");
    });
  }, [runId]);

  if (error) return <div className="error-banner" role="alert">{error}. A API não retornou dados alternativos inventados.</div>;
  if (!run) return <div className="empty-state"><strong>Carregando execução…</strong><p>Recuperando o contrato registrado da execução.</p></div>;

  const complete = run.status === "COMPLETED";
  return <>
    <div style={{ marginTop: 22 }}><StatusBadge tone={complete ? "success" : run.status === "FAILED" ? "critical" : "info"}>{statusLabel(run.status)}</StatusBadge></div>
    <section className="content-grid metrics-grid">
      <article className="metric-card"><span>Chamadas de ferramentas</span><strong>{run.tool_call_count}</strong><small>Limitadas pela política da aplicação</small></article>
      <article className="metric-card"><span>Tokens de entrada</span><strong>{run.input_tokens ?? "—"}</strong><small>Indisponíveis no modo determinístico</small></article>
      <article className="metric-card"><span>Tokens de saída</span><strong>{run.output_tokens ?? "—"}</strong><small>Indisponíveis no modo determinístico</small></article>
      <article className="metric-card"><span>Custo estimado</span><strong>{run.estimated_cost_usd == null ? "$—" : `$${run.estimated_cost_usd.toFixed(4)}`}</strong><small>Sem estimativa sintética</small></article>
    </section>
    <article className="panel" style={{ marginTop: 16 }}>
      <header className="panel-header"><h2>Registro da execução</h2><StatusBadge tone="neutral">{run.provider}</StatusBadge></header>
      <div className="panel-body summary-list">
        <div><span>ID da execução</span><b>{run.id}</b></div>
        <div><span>ID de rastreamento</span><b>{run.trace_id}</b></div>
        <div><span>Fluxo</span><b>{run.workflow}</b></div>
        <div><span>Modelo</span><b>{run.model}</b></div>
        <div><span>Iniciada</span><b>{formatPtDate(run.started_at)}</b></div>
        <div><span>Concluída</span><b>{run.completed_at ? formatPtDate(run.completed_at) : "Em execução"}</b></div>
        <div><span>Incidente</span><Link href={`/incidents/${run.incident_id}`}><b>{run.incident_id}</b></Link></div>
        <div><span>Erro</span><b>{run.error ?? "Nenhum registrado"}</b></div>
      </div>
    </article>
  </>;
}
