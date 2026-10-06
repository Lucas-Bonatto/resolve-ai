"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { CheckIcon, IncidentIcon, SparkIcon } from "@/components/icons";
import { StatusBadge } from "@/components/ui";
import { InvestigationTimeline } from "@/features/war-room/investigation-timeline";
import { API_URL, api } from "@/lib/api";
import { executionStatusLabel, incidentStateLabel, sourceTypeLabel, statusLabel, translateDemoText } from "@/lib/locale";
import type {
  Approval,
  Evidence,
  IncidentReport,
  IncidentSnapshot,
  RuntimeCapabilities,
  ValidationResult,
} from "@/types/domain";

const terminalStates = new Set(["RESOLVED", "FAILED", "ESCALATED"]);

function tone(state: string): "success" | "critical" | "warning" | "info" | "neutral" {
  if (state === "RESOLVED" || state === "COMPLETED") return "success";
  if (state === "FAILED" || state === "SEV-1") return "critical";
  if (state === "AWAITING_APPROVAL" || state === "ESCALATED") return "warning";
  if (["INVESTIGATING", "DIAGNOSING", "EXECUTING", "VALIDATING"].includes(state)) return "info";
  return "neutral";
}

function confidenceLabel(value: number): "Baixa" | "Média" | "Alta" {
  if (value >= 0.75) return "Alta";
  if (value >= 0.45) return "Média";
  return "Baixa";
}

function PendingDecision({
  approval,
  busy,
  mutationsAllowed,
  publicShowcase,
  onDecide,
}: {
  approval: Approval;
  busy: boolean;
  mutationsAllowed: boolean;
  publicShowcase: boolean;
  onDecide: (decision: "approve" | "reject") => void;
}) {
  return (
    <section className="war-card priority-card approval-live" aria-labelledby="pending-decision-title">
      <header className="war-card-head">
        <h3 id="pending-decision-title">Decisão necessária</h3>
        <StatusBadge tone="critical">Escrita crítica</StatusBadge>
      </header>
      <div className="war-card-body priority-card-grid">
        <div className="priority-card-primary">
          <span className="priority-eyebrow">Ponto de decisão humana</span>
          <h4>{translateDemoText(approval.requested_action)}</h4>
          <p>{translateDemoText(approval.reason)}</p>
          {!mutationsAllowed && <div className="runtime-notice" role="note"><strong>{publicShowcase ? "Vitrine pública somente leitura." : "Capacidades do ambiente indisponíveis."}</strong>{publicShowcase ? "Esta solicitação foi capturada no ponto de aprovação para inspeção; nenhuma decisão pode ser enviada por este ambiente." : "A decisão foi bloqueada por segurança porque a API não informou as capacidades deste ambiente."}</div>}
          <div className="approval-buttons">
            <button
              className="button button-danger"
              disabled={busy || !mutationsAllowed}
              onClick={() => onDecide("reject")}
            >
              Rejeitar reversão
            </button>
            <button
              className="button button-success"
              disabled={busy || !mutationsAllowed}
              onClick={() => onDecide("approve")}
            >
              <CheckIcon /> Aprovar reversão exata
            </button>
          </div>
        </div>
        <div className="priority-card-context">
          <div>
            <span className="detail-label">Impacto potencial</span>
            <p>{translateDemoText(approval.potential_impact)}</p>
          </div>
          <div>
            <span className="detail-label">Evidências</span>
            <div className="evidence-pills">
              {approval.evidence_ids.map(id => <span key={id}>{id}</span>)}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function ResolutionOutcome({
  validation,
  report,
}: {
  validation: ValidationResult;
  report: IncidentReport | null;
}) {
  return (
    <section
      className={`war-card priority-card outcome-card ${validation.passed ? "outcome-passed" : "outcome-failed"}`}
      aria-labelledby="resolution-outcome-title"
    >
      <header className="war-card-head">
        <h3 id="resolution-outcome-title">Resultado da resolução</h3>
        <StatusBadge tone={validation.passed ? "success" : "critical"}>
          {validation.passed ? "Validado" : "Falha na validação"}
        </StatusBadge>
      </header>
      <div className="war-card-body outcome-grid">
        <div className="outcome-summary">
          <span className="priority-eyebrow">Validação pós-remediação</span>
          <h4>{translateDemoText(validation.summary)}</h4>
          <div className="outcome-metrics" aria-label="Métricas de validação">
            <div><span>Verificações</span><b>{validation.checks_passed} passaram · {validation.checks_failed} falharam</b></div>
            <div><span>Transações recuperadas</span><b>{validation.recovered_transactions}</b></div>
          </div>
          <div className="evidence-pills" aria-label="Evidências de validação">
            {validation.evidence_ids.map(id => <span key={id}>{id}</span>)}
          </div>
        </div>
        {report && (
          <div className="outcome-report">
            <div className="outcome-report-heading">
              <h4>Relatório do incidente</h4>
              <StatusBadge tone={tone(report.final_status)}>{statusLabel(report.final_status)}</StatusBadge>
            </div>
            <p>{translateDemoText(report.summary)}</p>
            <div className="outcome-report-meta">
              <span>{report.evidence_ids.length} referências de evidência</span>
              <span>{report.hypothesis_ids.length} hipóteses consideradas</span>
              <span>Correlação {report.correlation_id}</span>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}

export function WarRoom({ incidentId }: { incidentId: string }) {
  const [snapshot, setSnapshot] = useState<IncidentSnapshot | null>(null);
  const [runtime, setRuntime] = useState<RuntimeCapabilities | null>(null);
  const [runtimeChecked, setRuntimeChecked] = useState(false);
  const [selected, setSelected] = useState<Evidence | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const evidenceButtonRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const evidenceHeadingRef = useRef<HTMLHeadingElement | null>(null);

  const refresh = useCallback(async () => {
    try {
      const next = await api.incident(incidentId);
      setSnapshot(next);
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Não foi possível atualizar o incidente");
    } finally {
      setLoading(false);
    }
  }, [incidentId]);

  useEffect(() => {
    let active = true;
    Promise.allSettled([api.incident(incidentId), api.runtime()])
      .then(([incidentResult, runtimeResult]) => {
        if (!active) return;
        if (incidentResult.status === "fulfilled") {
          setSnapshot(incidentResult.value);
          setError(null);
        }
        if (runtimeResult.status === "fulfilled") setRuntime(runtimeResult.value);
      })
      .finally(() => { if (active) { setRuntimeChecked(true); setLoading(false); } });
    return () => { active = false; };
  }, [incidentId]);

  const incidentState = snapshot?.incident.state;
  const lastEventId = snapshot?.events.at(-1)?.id;
  const mutationsAllowed = runtime?.mutations_allowed === true;
  const publicShowcase = runtime?.deployment_profile === "public_showcase";
  useEffect(() => {
    if (selected) evidenceHeadingRef.current?.focus();
  }, [selected]);

  useEffect(() => {
    if (!incidentState || terminalStates.has(incidentState) || !mutationsAllowed) return;
    const cursor = lastEventId ? `?after_id=${encodeURIComponent(lastEventId)}` : "";
    const events = new EventSource(`${API_URL}/api/incidents/${incidentId}/events/stream${cursor}`);
    events.addEventListener("incident", () => { void refresh(); });
    events.onerror = () => setError("O fluxo ao vivo foi interrompido. O ResolveAI tentará reconectar automaticamente.");
    return () => events.close();
  }, [incidentId, incidentState, lastEventId, mutationsAllowed, refresh]);

  const launch = async () => {
    if (!mutationsAllowed) return;
    setBusy(true); setError(null);
    try { await api.injectFlagship(); await refresh(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Não foi possível iniciar a demonstração"); }
    finally { setBusy(false); setLoading(false); }
  };

  const decide = async (decision: "approve" | "reject") => {
    if (!snapshot?.approval || !mutationsAllowed) return;
    setBusy(true); setError(null);
    try { await api.decide(snapshot.approval.id, decision); await refresh(); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Não foi possível registrar a decisão"); }
    finally { setBusy(false); }
  };

  const closeEvidence = () => {
    const evidenceId = selected?.id;
    setSelected(null);
    if (evidenceId) {
      requestAnimationFrame(() => evidenceButtonRefs.current[evidenceId]?.focus());
    }
  };

  if (loading) return <div className="launch-state"><div><div className="launch-orbit skeleton" /><div className="skeleton" style={{ height: 30, width: 270, margin: "0 auto 10px" }} /><div className="skeleton" style={{ height: 15, width: 390, maxWidth: "90%", margin: "0 auto" }} /></div></div>;
  if (!snapshot) return <div className="launch-state"><div><div className="launch-orbit"><IncidentIcon /></div><StatusBadge tone="critical">Cenário principal · SEV-1</StatusBadge><h2>Regressão no webhook de pagamentos</h2><p>{mutationsAllowed ? "Injete um incidente controlado e acompanhe o ResolveAI coletar evidências, testar hipóteses, pausar em uma reversão crítica e validar o resultado." : publicShowcase ? "A vitrine pública é somente leitura e deveria carregar um cenário determinístico para inspeção." : "Não foi possível verificar as capacidades deste ambiente; a injeção foi bloqueada por segurança."}</p>{mutationsAllowed && <button className="button button-primary" disabled={busy} onClick={launch}><SparkIcon /> {busy ? "Injetando…" : "Injetar incidente"}</button>}{error && <div className="error-banner" role="alert">{error}<br />Inicie a API com <code>make dev-api</code>.</div>}</div></div>;

  return <>
    <section className="war-header"><div><p className="breadcrumb">{snapshot.incident.id} / Sala de crise</p><h2>{translateDemoText(snapshot.incident.title)}</h2><p>{translateDemoText(snapshot.incident.description)}</p></div><div className="war-meta"><StatusBadge tone="critical">{snapshot.incident.severity}</StatusBadge><StatusBadge tone={tone(snapshot.incident.state)}>{incidentStateLabel(snapshot.incident.state)}</StatusBadge><StatusBadge tone="neutral">{executionStatusLabel(snapshot.incident.execution_status)}</StatusBadge></div></section>
    {runtimeChecked && !mutationsAllowed && <div className="runtime-notice runtime-notice-page" role="note"><strong>{publicShowcase ? "Modo de vitrine pública." : "Capacidades do ambiente indisponíveis."}</strong>{publicShowcase ? "Este snapshot fictício é reiniciado no servidor e todas as rotas de mutação são bloqueadas no backend." : "Ações mutáveis foram bloqueadas por segurança até que a API informe as capacidades do ambiente."}</div>}
    <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">Estado do incidente: {incidentStateLabel(snapshot.incident.state).toLowerCase()}.</p>
    {error && <div className="error-banner" role="alert">{error}</div>}
    {snapshot.approval?.status === "PENDING" && (
      <PendingDecision approval={snapshot.approval} busy={busy} mutationsAllowed={mutationsAllowed} publicShowcase={publicShowcase} onDecide={decide} />
    )}
    {snapshot.validation && (
      <ResolutionOutcome validation={snapshot.validation} report={snapshot.report} />
    )}
    <div className="war-grid">
      <aside className="war-column">
        <section className="war-card"><header className="war-card-head"><h3>Resumo do incidente</h3><StatusBadge tone="neutral">Ao vivo</StatusBadge></header><div className="war-card-body summary-list"><div><span>Serviço afetado</span><b>{snapshot.incident.affected_service}</b></div><div><span>Clientes</span><b>{snapshot.incident.affected_customers}</b></div><div><span>Evidências</span><b>{snapshot.evidence.length} registros</b></div><div><span>Chamadas de ferramentas</span><b>{snapshot.tool_calls.length}</b></div><div><span>Provedor</span><b>{snapshot.run?.provider ?? "Iniciando"}</b></div><div><span>ID de correlação</span><b>{snapshot.incident.correlation_id}</b></div><div><span>ID de rastreamento</span>{snapshot.run ? <Link href={`/runs/${snapshot.run.id}`}><b>{snapshot.run.trace_id}</b></Link> : <b>—</b>}</div></div></section>
        <section className="war-card"><header className="war-card-head"><h3>Repositório de evidências</h3><span className="status-badge status-neutral">{snapshot.evidence.length}</span></header><div className="war-card-body evidence-grid">{snapshot.evidence.length ? snapshot.evidence.map(item => <button className="evidence-button" key={item.id} ref={node => { evidenceButtonRefs.current[item.id] = node; }} onClick={() => setSelected(item)} aria-label={`Inspecionar evidência ${item.id}`} aria-expanded={selected?.id === item.id} aria-controls={selected?.id === item.id ? "selected-evidence-detail" : undefined}><span className="evidence-type">{sourceTypeLabel(item.source_type)}</span><span><b>{item.id}</b><span>{translateDemoText(item.title)}</span></span><strong>{Math.round(item.relevance * 100)}%</strong></button>) : <div className="empty-state"><strong>Nenhuma evidência coletada.</strong><p>As evidências aparecerão quando resultados validados de ferramentas entrarem no registro do incidente.</p></div>}</div></section>
        {selected && <section className="war-card" id="selected-evidence-detail" aria-labelledby="selected-evidence-title"><header className="war-card-head"><h3 id="selected-evidence-title" tabIndex={-1} ref={evidenceHeadingRef}>{selected.id}</h3><button className="button button-secondary evidence-close" onClick={closeEvidence}>Fechar evidência</button></header><div className="war-card-body"><p style={{ fontSize: 11, lineHeight: 1.55, marginTop: 0 }}>{translateDemoText(selected.summary)}</p><pre tabIndex={0} aria-label={`Payload estruturado da evidência ${selected.id}`} style={{ overflow: "auto", fontSize: 9, background: "#f4f6f2", padding: 10, borderRadius: 8 }}>{JSON.stringify(selected.raw_payload, null, 2)}</pre></div></section>}
      </aside>

      <section className="war-column" aria-label="Investigação">
        <InvestigationTimeline events={snapshot.events} />
        {snapshot.diagnosis && <section className="diagnosis-card"><small>Resumo da decisão · Confiança heurística {confidenceLabel(snapshot.diagnosis.confidence).toLowerCase()} · {statusLabel(snapshot.diagnosis.outcome)}</small><h3>{translateDemoText(snapshot.diagnosis.probable_root_cause)}</h3><p>{translateDemoText(snapshot.diagnosis.summary)} {translateDemoText(snapshot.diagnosis.recommended_next_step)}</p><div className="evidence-pills">{snapshot.diagnosis.evidence_ids.map(id => <span key={id}>{id}</span>)}</div></section>}
        {snapshot.remediation_plan && <section className="war-card"><header className="war-card-head"><h3>Plano de remediação</h3><StatusBadge tone="critical">Crítico</StatusBadge></header><div className="war-card-body"><p style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.55 }}>{translateDemoText(snapshot.remediation_plan.summary)}</p>{snapshot.remediation_plan.steps.map((step, index) => <div className="service-row" key={step.id}><span><b>{index + 1}. {translateDemoText(step.title)}</b><br /><small>{translateDemoText(step.description)}</small></span><StatusBadge tone={step.status === "SIMULATED" ? "success" : step.risk_level === "critical_write" ? "critical" : "neutral"}>{executionStatusLabel(step.status)}</StatusBadge></div>)}</div></section>}
      </section>

      <aside className="war-column">
        <section className="war-card"><header className="war-card-head"><h3>Motor de hipóteses</h3><span className="status-badge status-neutral">{snapshot.hypotheses.length}</span></header><div className="war-card-body">{snapshot.hypotheses.length ? snapshot.hypotheses.map(item => <article className="hypothesis" key={item.id}><div className="hypothesis-head"><h4>{translateDemoText(item.title)}</h4><small>{confidenceLabel(item.confidence)} · {statusLabel(item.status)}</small></div><div className="confidence-bar"><span style={{ width: `${item.confidence * 100}%` }} /></div><p>{translateDemoText(item.description)}</p><small>Verificar: {translateDemoText(item.verification_strategy)}</small>{(item.evidence_for.length > 0 || item.evidence_against.length > 0) && <div className="evidence-pills" aria-label={`Evidências da hipótese ${translateDemoText(item.title)}`}>{item.evidence_for.map(id => <span key={`for-${id}`}>Sustenta {id}</span>)}{item.evidence_against.map(id => <span key={`against-${id}`}>Contesta {id}</span>)}</div>}</article>) : <div className="empty-state"><strong>As hipóteses estão sendo formadas.</strong><p>O ResolveAI não salta diretamente para uma causa raiz.</p></div>}</div></section>
        {snapshot.approval?.status !== "PENDING" && <section className="war-card"><header className="war-card-head"><h3>Aprovações humanas</h3></header><div className="empty-state"><strong>{snapshot.approval ? `Decisão: ${statusLabel(snapshot.approval.status)}` : "Nenhuma decisão aguardando você."}</strong><p>{snapshot.approval ? `Registrada para: ${translateDemoText(snapshot.approval.requested_action)}.` : "O ResolveAI não possui ação crítica aguardando aprovação."}</p></div></section>}
        <section className="war-card"><header className="war-card-head"><h3>Limite de permissões</h3><StatusBadge tone="success">Aplicado</StatusBadge></header><div className="war-card-body summary-list"><div><span>Ferramentas de leitura</span><b>Automáticas</b></div><div><span>Escritas seguras</span><b>Auditadas</b></div><div><span>Escritas críticas</span><b>Aprovação</b></div><div><span>Responsável pela política</span><b>Backend</b></div></div></section>
      </aside>
    </div>
  </>;
}
