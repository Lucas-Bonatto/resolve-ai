"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowIcon } from "@/components/icons";
import { MetricCard, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { services } from "@/lib/demo-data";
import { executionStatusLabel, incidentStateLabel, translateDemoText } from "@/lib/locale";
import type { EvaluationRun, Incident, IncidentState } from "@/types/domain";

const terminalStates = new Set<IncidentState>(["RESOLVED", "FAILED", "ESCALATED"]);

function incidentTone(state: IncidentState): "neutral" | "critical" | "warning" | "success" | "info" {
  if (state === "RESOLVED") return "success";
  if (state === "FAILED") return "critical";
  if (state === "AWAITING_APPROVAL" || state === "ESCALATED") return "warning";
  if (state === "NEW") return "neutral";
  return "info";
}

function DashboardLoading() {
  return <>
    <section className="content-grid metrics-grid" aria-label="Carregando métricas operacionais ao vivo">
      {[0, 1, 2, 3].map(item => <article className="metric-card" key={item}><div className="skeleton" style={{ height: 12, width: "62%" }} /><div className="skeleton" style={{ height: 34, width: "48%", marginTop: "auto" }} /></article>)}
    </section>
    <div className="dashboard-loading panel"><div className="skeleton" /><span>Carregando estado da demonstração…</span></div>
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
        setIncidentError(incidentResult.status === "rejected" ? incidentResult.reason instanceof Error ? incidentResult.reason.message : "A solicitação de incidentes falhou" : null);
        setEvaluationError(evaluationResult.status === "rejected" ? evaluationResult.reason instanceof Error ? evaluationResult.reason.message : "A solicitação de avaliações falhou" : null);
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
  const errors = [incidentError && `Incidentes: ${incidentError}`, evaluationError && `Avaliações: ${evaluationError}`].filter(Boolean).join("; ");

  return <>
    {errors && <div className="error-banner" role="alert">Alguns dados ao vivo estão indisponíveis: {errors}. As áreas com dados de exemplo continuam identificadas abaixo.</div>}
    <section className="content-grid metrics-grid" aria-label="Métricas operacionais ao vivo">
      <MetricCard label="Incidentes abertos" value={incidentError ? "Indisponível" : String(openIncidents.length)} detail={incidentError ? "Falha na API de incidentes" : "Processo atual da demonstração"} tone={!incidentError && openIncidents.length ? "warn" : !incidentError ? "good" : "default"} />
      <MetricCard label="Resolvidos nesta sessão" value={incidentError ? "Indisponível" : String(resolvedIncidents.length)} detail={incidentError ? "Falha na API de incidentes" : "Incidentes terminais validados"} tone={!incidentError && resolvedIncidents.length ? "good" : "default"} />
      <MetricCard label="Avaliação mais recente" value={evaluationError ? "Indisponível" : latestRun ? `${passed}/${latestRun.results.length}` : "Não executada"} detail={evaluationError ? "Falha na API de avaliações" : latestRun ? `${failures} ${failures === 1 ? "falha visível" : "falhas visíveis"}` : "Nenhum resultado executado neste processo"} tone={!evaluationError && failures ? "warn" : !evaluationError && latestRun ? "good" : "default"} />
      <MetricCard label="Violações de política crítica" value={evaluationError ? "Indisponível" : criticalViolations === null ? "Não medido" : String(criticalViolations)} detail={evaluationError ? "Falha na API de avaliações" : latestRun ? `${probes} sondagens ativas de limite` : "Execute a Central de avaliações para medir"} tone={!evaluationError && criticalViolations === 0 ? "good" : !evaluationError && criticalViolations ? "warn" : "default"} />
    </section>

    <section className="content-grid dashboard-main">
      <div className="stack">
        <article className="panel"><header className="panel-header"><h2>Fila de incidentes ao vivo</h2><Link href="/incidents">Ver todos <ArrowIcon /></Link></header>
          {incidents.length ? incidents.map(incident => <Link href={`/incidents/${incident.id}`} className="incident-row" key={incident.id}><div><h3>{translateDemoText(incident.title)}</h3><p>{incident.id} · {incident.affected_service} · {incident.affected_customers} afetados</p></div><StatusBadge tone={incidentTone(incident.state)}>{incident.severity}</StatusBadge><div>{incidentStateLabel(incident.state)}<br /><small>{executionStatusLabel(incident.execution_status)}</small></div></Link>) : <div className="empty-state"><strong>{incidentError ? "O estado dos incidentes ao vivo está indisponível." : "Nenhum incidente foi injetado neste processo."}</strong><p>{incidentError ? "Inicie a API para restaurar a visão operacional ao vivo." : "Abra o cenário principal para iniciar o fluxo determinístico."}</p></div>}
        </article>
        <article className="panel"><header className="panel-header"><h2>Atividade recente do agente</h2><StatusBadge tone="neutral">Histórico de exemplo</StatusBadge></header><div className="panel-body activity-list">
          <div className="activity-item"><b>INC-2026-0038 · Resolução validada</b><p>A rotação da chave de autenticação foi concluída após aprovação do operador.</p></div>
          <div className="activity-item"><b>INC-2026-0031 · Evidências coletadas</b><p>Profundidade da fila, atraso do consumidor e janela de implantação foram correlacionados.</p></div>
          <div className="activity-item"><b>Execução da avaliação · 40 casos</b><p>Falhas permanecem visíveis por caso sempre que um contrato determinístico não é atendido.</p></div>
        </div></article>
      </div>
      <div className="stack">
        <article className="panel"><header className="panel-header"><h2>Saúde dos serviços</h2><StatusBadge tone="neutral">Dados de exemplo</StatusBadge></header><div className="panel-body">{services.map(service => <div className="service-row" key={service.name}><span><i className={`health-dot ${service.status === "Degradado" ? "degraded" : ""}`} />{service.name}</span><small>{service.latency}</small></div>)}</div></article>
        <article className="panel"><header className="panel-header"><h2>Postura da avaliação</h2><Link href="/evals">Abrir central</Link></header><div className="panel-body"><div className="diagnosis-card"><small>{evaluationError ? "Avaliação indisponível" : latestRun ? "Resultado determinístico executado" : "Não executada neste processo"}</small><h3>{evaluationError ? "Não foi possível verificar o resultado" : latestRun ? `${passed} de ${latestRun.results.length} casos passaram` : "Execute antes de divulgar resultados"}</h3><p>{evaluationError ? "A solicitação à API de avaliações falhou; nenhuma afirmação sobre o benchmark é exibida." : latestRun ? `${failures === 0 ? "Nenhuma regressão conhecida está visível" : failures === 1 ? "Uma regressão conhecida permanece visível" : `${failures} regressões conhecidas permanecem visíveis`}. Revisão do código: ${latestRun.code_revision}.` : "A Central de avaliações calcula os resultados dos cenários e testa ativamente o gateway de políticas críticas."}</p><div className="evidence-pills"><span>{evaluationError ? "INDISPONÍVEL" : latestRun ? `${latestRun.results.length} CASOS` : "NÃO EXECUTADA"}</span><span>{evaluationError ? "SEM AFIRMAÇÃO" : latestRun ? `${probes} SONDAGENS DE LIMITE` : "SEM MEDIÇÃO"}</span><span>{evaluationError ? "REPETIR" : latestRun ? `${failures} ${failures === 1 ? "FALHA" : "FALHAS"}` : "EXECUÇÃO NECESSÁRIA"}</span></div></div></div></article>
      </div>
    </section>
  </>;
}
