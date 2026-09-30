import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { ArrowIcon, SparkIcon } from "@/components/icons";
import { MetricCard, StatusBadge } from "@/components/ui";
import { incidentFixtures, services } from "@/lib/demo-data";

export const metadata = { title: "Command center" };

export default function DashboardPage() {
  return <AppShell title="Command center" description="Operational posture across the fictional NovaPay environment." actions={<Link className="button button-primary" href="/incidents/INC-2026-0042"><SparkIcon /> Inject incident</Link>}>
    <section className="content-grid metrics-grid" aria-label="Operational metrics">
      <MetricCard label="Open incidents" value="1" detail="1 awaiting demo launch" tone="warn" />
      <MetricCard label="Resolved · 30d" value="18" detail="Deterministic fixture history" />
      <MetricCard label="Mean investigation" value="02:46" detail="Generated demo run history" />
      <MetricCard label="Approval bypass" value="0%" detail="Last executed benchmark" tone="good" />
    </section>

    <section className="content-grid dashboard-main">
      <div className="stack">
        <article className="panel"><header className="panel-header"><h2>Incident queue</h2><Link href="/incidents">View all <ArrowIcon /></Link></header>
          {incidentFixtures.map((incident, index) => <Link href={`/incidents/${incident.id}`} className="incident-row" key={incident.id}><div><h3>{incident.title}</h3><p>{incident.id} · {incident.service} · {incident.impact}</p></div><StatusBadge tone={index === 0 ? "critical" : incident.status === "Resolved" ? "success" : "warning"}>{incident.severity}</StatusBadge><div>{incident.status}<br /><small>{incident.age}</small></div></Link>)}
        </article>
        <article className="panel"><header className="panel-header"><h2>Recent agent activity</h2><span className="status-badge status-neutral">Fixture history</span></header><div className="panel-body activity-list">
          <div className="activity-item"><b>INC-2026-0038 · Resolution validated</b><p>Authentication key rotation completed after operator approval.</p></div>
          <div className="activity-item"><b>INC-2026-0031 · Evidence collected</b><p>Queue depth, consumer lag, and deployment window correlated.</p></div>
          <div className="activity-item"><b>Evaluation run · 40 cases</b><p>One known false-correlation regression remains visible for review.</p></div>
        </div></article>
      </div>
      <div className="stack">
        <article className="panel"><header className="panel-header"><h2>Service health</h2><StatusBadge tone="warning">1 degraded</StatusBadge></header><div className="panel-body">{services.map(service => <div className="service-row" key={service.name}><span><i className={`health-dot ${service.status === "Degraded" ? "degraded" : ""}`} />{service.name}</span><small>{service.latency}</small></div>)}</div></article>
        <article className="panel"><header className="panel-header"><h2>Evaluation posture</h2><Link href="/evals">Open center</Link></header><div className="panel-body"><div className="diagnosis-card"><small>Last executed locally</small><h3>Security invariants held</h3><p>Unauthorized critical execution: 0. One diagnosis regression remains visible rather than hidden.</p><div className="evidence-pills"><span>40 CASES</span><span>5 INJECTION</span><span>0 BYPASS</span></div></div></div></article>
      </div>
    </section>
  </AppShell>;
}
