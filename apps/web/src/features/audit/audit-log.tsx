"use client";

import { useEffect, useState } from "react";
import { StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";

export function AuditLog() {
  const [records, setRecords] = useState<Array<Record<string, unknown>>>([]);
  const [error, setError] = useState(false);
  useEffect(() => { api.audit().then(setRecords).catch(() => setError(true)); }, []);
  if (error) return <div className="error-banner" role="alert">The audit API is offline. Start it with <code>make dev-api</code>. No records were fabricated.</div>;
  return <article className="panel" style={{ marginTop: 22 }}>{records.length ? <div className="table-scroll" role="region" aria-label="Audit records table" tabIndex={0}><table className="data-table"><caption className="sr-only">Audit records</caption><thead><tr><th>Timestamp</th><th>Actor</th><th>Action</th><th>Resource</th><th>Result</th><th>Risk</th></tr></thead><tbody>{records.map(record => <tr key={String(record.id)}><td><small>{new Date(String(record.timestamp)).toLocaleString()}</small></td><td><strong>{String(record.actor_type)}</strong><small>{String(record.actor_id)}</small></td><td>{String(record.action)}</td><td>{String(record.resource_type)} · {String(record.resource_id)}</td><td><StatusBadge tone={String(record.result).includes("BLOCK") ? "critical" : "neutral"}>{String(record.result)}</StatusBadge></td><td>{record.risk_level ? String(record.risk_level) : "—"}</td></tr>)}</tbody></table></div> : <div className="empty-state"><strong>No audit records yet.</strong><p>Launch the flagship incident to create append-only workflow, tool, and approval records.</p></div>}</article>;
}
