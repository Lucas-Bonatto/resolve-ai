"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { AuditIcon, EvalIcon, IncidentIcon, LockIcon, MarkIcon, PulseIcon } from "./icons";

const navigation = [
  { href: "/dashboard", label: "Central de operações", icon: PulseIcon },
  { href: "/incidents", label: "Incidentes", icon: IncidentIcon },
  { href: "/evals", label: "Avaliações", icon: EvalIcon },
  { href: "/security", label: "Segurança", icon: LockIcon },
  { href: "/audit", label: "Auditoria", icon: AuditIcon },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || (href === "/incidents" && pathname.startsWith("/incidents/"));
}

export function AppNavigation() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return <aside className={`sidebar${open ? " sidebar-open" : ""}`}>
    <div className="sidebar-top">
      <Link href="/" className="brand" aria-label="Página inicial do ResolveAI"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link>
      <button className="sidebar-toggle" type="button" aria-expanded={open} aria-controls="primary-navigation" onClick={() => setOpen(value => !value)}>
        <span className="sidebar-toggle-icon" aria-hidden="true"><i /><i /><i /></span>
        <span>{open ? "Fechar" : "Menu"}</span>
      </button>
    </div>
    <div className="environment"><span className="live-dot" /> Ambiente de demonstração <b>Simulado · SIMULATED</b></div>
    <nav id="primary-navigation" aria-label="Navegação principal">
      {navigation.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return <Link key={href} href={href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined} onClick={() => setOpen(false)}><Icon />{label}</Link>;
      })}
    </nav>
    <div className="sidebar-foot"><p>Operações NovaPay</p><span>Todas as entidades são fictícias.</span><kbd>⌘ K</kbd><small>Ações rápidas</small></div>
  </aside>;
}
