"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuditIcon, EvalIcon, IncidentIcon, LockIcon, MarkIcon, PulseIcon } from "./icons";

const navigation = [
  { href: "/dashboard", label: "Command center", icon: PulseIcon },
  { href: "/incidents", label: "Incidents", icon: IncidentIcon },
  { href: "/evals", label: "Evaluation", icon: EvalIcon },
  { href: "/security", label: "Security", icon: LockIcon },
  { href: "/audit", label: "Audit log", icon: AuditIcon },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || (href === "/incidents" && pathname.startsWith("/incidents/"));
}

export function AppNavigation() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return <aside className={`sidebar${open ? " sidebar-open" : ""}`}>
    <div className="sidebar-top">
      <Link href="/" className="brand" aria-label="ResolveAI home"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link>
      <button className="sidebar-toggle" type="button" aria-expanded={open} aria-controls="primary-navigation" onClick={() => setOpen(value => !value)}>
        <span className="sidebar-toggle-icon" aria-hidden="true"><i /><i /><i /></span>
        <span>{open ? "Close" : "Menu"}</span>
      </button>
    </div>
    <div className="environment"><span className="live-dot" /> Demo environment <b>SIMULATED</b></div>
    <nav id="primary-navigation" aria-label="Primary navigation">
      {navigation.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return <Link key={href} href={href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined} onClick={() => setOpen(false)}><Icon />{label}</Link>;
      })}
    </nav>
    <div className="sidebar-foot"><p>NovaPay operations</p><span>All entities are fictional.</span><kbd>⌘ K</kbd><small>Quick actions</small></div>
  </aside>;
}
