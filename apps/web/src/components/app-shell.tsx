import Link from "next/link";
import type { ReactNode } from "react";
import { AuditIcon, EvalIcon, IncidentIcon, LockIcon, MarkIcon, PulseIcon } from "./icons";

const navigation = [
  { href: "/dashboard", label: "Command center", icon: PulseIcon },
  { href: "/incidents", label: "Incidents", icon: IncidentIcon },
  { href: "/evals", label: "Evaluation", icon: EvalIcon },
  { href: "/security", label: "Security", icon: LockIcon },
  { href: "/audit", label: "Audit log", icon: AuditIcon },
];

export function AppShell({ children, title, description, actions }: { children: ReactNode; title: string; description: string; actions?: ReactNode }) {
  return <div className="app-layout">
    <aside className="sidebar">
      <Link href="/" className="brand"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link>
      <div className="environment"><span className="live-dot" /> Demo environment <b>SIMULATED</b></div>
      <nav aria-label="Primary navigation">
        {navigation.map(({ href, label, icon: Icon }) => <Link key={href} href={href}><Icon />{label}</Link>)}
      </nav>
      <div className="sidebar-foot"><p>NovaPay operations</p><span>All entities are fictional.</span><kbd>⌘ K</kbd><small>Quick actions</small></div>
    </aside>
    <main className="app-main">
      <header className="app-header"><div><p className="breadcrumb">NovaPay / Operations</p><h1>{title}</h1><p>{description}</p></div>{actions && <div className="header-actions">{actions}</div>}</header>
      {children}
    </main>
  </div>;
}
