"use client";

import { useEffect, useState } from "react";
import { EvalIcon } from "@/components/icons";
import { MetricCard, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { translateDemoText } from "@/lib/locale";
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

const timestamp = (value: string) => new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "medium",
  timeStyle: "medium",
  timeZone: "UTC",
}).format(new Date(value));

const revision = (value: string) => value === "unknown" ? "Não configurada" : value;

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
      setError(requestError instanceof Error ? requestError.message : "A avaliação falhou");
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
  const failureLabel = `${failures.length} ${failures.length === 1 ? "falha" : "falhas"}`;
  const liveMessage = running
    ? "Avaliação em execução. 40 casos na fila."
    : run.sample_data
      ? "Nenhuma avaliação foi executada neste processo."
      : `Avaliação concluída. ${passed} de ${total} casos passaram. ${failureLabel}.`;

  return <>
    <div className="evaluation-topbar" aria-busy={running}>
      <div>
        <StatusBadge tone={resultTone}>{run.sample_data ? "Dados de exemplo" : "Resultado executado"}</StatusBadge>
        <p>{run.provider} · {run.model} · {run.metrics.case_count ?? total} casos</p>
      </div>
      <button className="button button-primary" disabled={running} onClick={execute}>
        <EvalIcon />{running ? "Executando 40 casos…" : "Executar avaliação"}
      </button>
    </div>
    <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{liveMessage}</p>
    {error && <div className="error-banner" role="alert">{error}. Inicie a API com <code>make dev-api</code>.</div>}
    <section className={`evaluation-summary ${run.sample_data ? "evaluation-summary-empty" : failures.length ? "evaluation-summary-warning" : "evaluation-summary-success"}`} aria-labelledby="evaluation-result-title">
      <div>
        <span className="priority-eyebrow">Contrato determinístico de avaliação</span>
        <h2 id="evaluation-result-title">{run.sample_data ? "Nenhuma avaliação executada neste processo" : `${passed} / ${total} casos passaram`}</h2>
        <p>{run.sample_data ? "Execute a suíte para produzir um resultado auditável no processo atual da API." : failures.length ? "A execução terminou com uma regressão visível. As metas de segurança permanecem separadas da precisão dos cenários." : "A execução terminou sem regressão visível de contrato."}</p>
      </div>
      <dl className="evaluation-provenance">
        <div><dt>Executada</dt><dd>{run.sample_data ? "Aguardando execução" : `${timestamp(run.created_at)} UTC`}</dd></div>
        <div><dt>Revisão do código</dt><dd>{revision(run.code_revision)}</dd></div>
        <div><dt>Sondagens de limite</dt><dd>{run.sample_data ? "—" : probeCount}</dd></div>
        <div><dt>Duração média por caso</dt><dd>{run.sample_data ? "—" : `${averageDuration.toFixed(1)} ms`}</dd></div>
      </dl>
    </section>
    <section className="content-grid eval-metrics">
      <MetricCard label="Sucesso do contrato de cenários" value={run.sample_data ? "—" : percent(run.metrics.scenario_contract_success_rate)} detail="Casos aprovados / casos executados" tone={scoreTone} />
      <MetricCard label="Causa raiz top-1" value={run.sample_data ? "—" : percent(run.metrics.root_cause_top_1_accuracy)} detail="Verdade esperada determinística" tone={failures.length ? "warn" : "good"} />
      <MetricCard label="Cobertura de evidências" value={run.sample_data ? "—" : percent(run.metrics.required_evidence_recall)} detail="IDs obrigatórios encontrados" tone={(run.metrics.required_evidence_recall ?? 0) < 1 && !run.sample_data ? "warn" : "good"} />
      <MetricCard label="Violações de evidência" value={run.sample_data ? "—" : String(run.metrics.evidence_integrity_violations ?? 0)} detail="Meta de segurança: 0" tone={(run.metrics.evidence_integrity_violations ?? 0) > 0 ? "warn" : "good"} />
      <MetricCard label="Bypass por injeção de prompt" value={run.sample_data ? "—" : String(run.metrics.prompt_injection_bypasses ?? 0)} detail={`${probeCount || "—"} sondagens ativas de limite · meta 0`} tone={(run.metrics.prompt_injection_bypasses ?? 0) > 0 ? "warn" : "good"} />
      <MetricCard label="Escritas não autorizadas" value={run.sample_data ? "—" : String(run.metrics.unauthorized_critical_tool_execution ?? 0)} detail={`${probeCount || "—"} sondagens ativas de limite · meta 0`} tone={(run.metrics.unauthorized_critical_tool_execution ?? 0) > 0 ? "warn" : "good"} />
    </section>
    <section className="content-grid dashboard-main">
      <article className="panel"><header className="panel-header"><h2>Cobertura do benchmark</h2><StatusBadge tone="info">Avaliadores determinísticos</StatusBadge></header><div className="bar-chart">{[
        ["Pagamentos", 10], ["Confiabilidade", 10], ["Banco", 5], ["Auth + fila", 5], ["Segurança", 5], ["Insuficiente", 5],
      ].map(([label, value]) => <div className="bar-column" key={label}><b>{value}</b><div className="bar" style={{ height: `${Number(value) * 12}px` }} /><span>{label}</span></div>)}</div></article>
      <article className="panel"><header className="panel-header"><h2>Proveniência da execução</h2><StatusBadge tone="neutral">{run.sample_data ? "Não executada" : "Executada"}</StatusBadge></header><div className="panel-body summary-list"><div><span>Provedor</span><b>{run.provider}</b></div><div><span>Modelo</span><b>{run.model}</b></div><div><span>Tipo de execução</span><b>{run.run_kind}</b></div><div><span>Suíte</span><b>{run.suite_version}</b></div><div><span>Revisão do código</span><b>{revision(run.code_revision)}</b></div><div><span>Executada em</span><b>{run.sample_data ? "Não executada" : `${timestamp(run.created_at)} UTC`}</b></div><div><span>Casos</span><b>{total}</b></div><div><span>Regressões conhecidas</span><b>{failures.length}</b></div><div><span>ID do resultado</span><b>{run.id}</b></div></div></article>
    </section>
    <article className="panel evaluation-comparison"><header className="panel-header"><h2>Comparação com a execução anterior</h2><StatusBadge tone="neutral">Histórico do processo</StatusBadge></header>{previous ? <div className="panel-body summary-list"><div><span>Resultado anterior</span><b>{previousPassed} / {previous.results.length} passaram</b></div><div><span>Diferença de aprovações</span><b>{delta > 0 ? `+${delta}` : delta} casos</b></div><div><span>Revisão anterior</span><b>{revision(previous.code_revision)}</b></div><div><span>ID do resultado anterior</span><b>{previous.id}</b></div></div> : <div className="empty-state"><strong>Nenhuma execução anterior neste processo.</strong><p>Execute novamente a suíte determinística para comparar resultados. A reinicialização da demonstração limpa este histórico local intencionalmente.</p></div>}</article>
    <article className="panel evaluation-failures"><header className="panel-header"><h2 id="failing-cases-title">Casos com falha permanecem visíveis</h2><StatusBadge tone={run.sample_data ? "neutral" : failures.length ? "warning" : "success"}>{run.sample_data ? "Não executada" : failureLabel}</StatusBadge></header>{failures.length ? <div className="table-scroll" role="region" aria-labelledby="failing-cases-title" tabIndex={0}><table className="data-table"><caption className="sr-only">Casos de avaliação com falha</caption><thead><tr><th>Caso</th><th>Resultado</th><th>Cobertura de evidências</th><th>Motivo da falha</th></tr></thead><tbody>{failures.map(item => <tr key={item.case_id}><td><strong>{item.case_id}</strong></td><td><StatusBadge tone="critical">Falhou</StatusBadge></td><td>{percent(item.evidence_recall)}</td><td>{item.failure_reason ? translateDemoText(item.failure_reason) : "—"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>{run.sample_data ? "Nenhuma avaliação foi executada neste processo." : "Nenhum caso falhou nesta execução."}</strong><p>{run.sample_data ? "Execute a suíte determinística para calcular as métricas do produto e de segurança." : "Compare com a execução anterior antes de promover um provedor ou alterar um prompt."}</p></div>}</article>
  </>;
}
