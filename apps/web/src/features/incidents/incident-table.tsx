"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { SearchIcon } from "@/components/icons";
import { StatusBadge } from "@/components/ui";
import { incidentFixtures } from "@/lib/demo-data";

export function IncidentTable() {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("all");
  const incidents = useMemo(() => incidentFixtures.filter(item => {
    const matches = `${item.id} ${item.title} ${item.service}`.toLowerCase().includes(query.toLowerCase());
    return matches && (severity === "all" || item.severity === severity);
  }), [query, severity]);

  return <>
    <div className="toolbar"><label className="search-field"><SearchIcon /><span className="sr-only">Search incidents</span><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search incidents, services, IDs…" /></label><select value={severity} onChange={event => setSeverity(event.target.value)} aria-label="Filter by severity"><option value="all">All severities</option><option>SEV-1</option><option>SEV-2</option><option>SEV-3</option></select><select aria-label="Filter by state"><option>All states</option><option>Resolved</option><option>Escalated</option></select></div>
    <p className="sr-only" role="status" aria-live="polite" aria-atomic="true">{incidents.length} incidents match the current filters.</p>
    <article className="panel" style={{ marginTop: 14 }}><div className="table-scroll" role="region" aria-label="Incident results table" tabIndex={0}><table className="data-table"><caption className="sr-only">Incident results</caption><thead><tr><th>Incident</th><th>Severity</th><th>Status</th><th>Service</th><th>Impact</th><th>Created</th></tr></thead><tbody>{incidents.map((item, index) => <tr key={item.id}><td><Link href={`/incidents/${item.id}`}><strong>{item.title}</strong><small>{item.id}</small></Link></td><td><StatusBadge tone={index === 0 ? "critical" : "warning"}>{item.severity}</StatusBadge></td><td>{item.status}</td><td>{item.service}</td><td>{item.impact}</td><td>{item.age}</td></tr>)}</tbody></table></div>{incidents.length === 0 && <div className="empty-state"><strong>No incidents match these filters.</strong><p>Change the search or severity filter to broaden the result set.</p></div>}</article>
  </>;
}
