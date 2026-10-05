"use client";

import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { executionStatusLabel, formatPtDate, riskLevelLabel } from "@/lib/locale";

export function AuditLog() {
  const [records, setRecords] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState(false);
  useEffect(() => { api.audit().then(setRecords).catch(() => setError(true)); }, []);
  if (error) return <div className="error-banner" role="alert">A API de auditoria está offline. Inicie-a com <code>make dev-api</code>. Nenhum registro foi inventado.</div>;
  return <article className="panel" style={{ marginTop: 22 }}>{records.length ? <div className="table-scroll" role="region" aria-label="Tabela de registros de auditoria" tabIndex={0}><table className="data-table"><caption className="sr-only">Registros de auditoria</caption><thead><tr><th>Data e hora</th><th>Ator</th><th>Ação</th><th>Recurso</th><th>Resultado</th><th>Risco</th></tr></thead><tbody>{records.map(record => <tr key={String(record.id)}><td><small>{formatPtDate(String(record.timestamp))}</small></td><td><strong>{String(record.actor_type)}</strong><small>{String(record.actor_id)}</small></td><td>{String(record.action)}</td><td>{String(record.resource_type)} · {String(record.resource_id)}</td><td><StatusBadge tone={String(record.result).includes("BLOCK") ? "critical" : "neutral"}>{executionStatusLabel(String(record.result))}</StatusBadge></td><td>{record.risk_level ? riskLevelLabel(String(record.risk_level)) : "—"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>Ainda não há registros de auditoria.</strong><p>Inicie o incidente principal para criar registros anexáveis de fluxo, ferramentas e aprovações.</p></div>}</article>;
}
