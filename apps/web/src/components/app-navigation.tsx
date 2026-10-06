"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { RuntimeCapabilities } from "@/types/domain";
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
  const [runtime, setRuntime] = useState<RuntimeCapabilities | null>(null);
  const [runtimeChecked, setRuntimeChecked] = useState(false);

  useEffect(() => {
    let active = true;
    api.runtime()
      .then(value => { if (active) setRuntime(value); })
      .catch(() => undefined)
      .finally(() => { if (active) setRuntimeChecked(true); });
    return () => { active = false; };
  }, []);

  const publicShowcase = runtime?.deployment_profile === "public_showcase";
  const environmentLabel = runtime
    ? publicShowcase ? "Vitrine pública" : "Ambiente de demonstração"
    : runtimeChecked ? "Ambiente indisponível" : "Verificando ambiente";
  const environmentDetail = runtime
    ? publicShowcase ? "Somente leitura" : "Simulado · SIMULATED"
    : runtimeChecked ? "Controles bloqueados" : "Aguarde";

  return <aside className={`sidebar${open ? " sidebar-open" : ""}`}>
    <div className="sidebar-top">
      <Link href="/" className="brand" aria-label="Página inicial do ResolveAI"><span className="brand-mark"><MarkIcon /></span><span>Resolve<span>AI</span></span></Link>
      <button className="sidebar-toggle" type="button" aria-expanded={open} aria-controls="primary-navigation" onClick={() => setOpen(value => !value)}>
        <span className="sidebar-toggle-icon" aria-hidden="true"><i /><i /><i /></span>
        <span>{open ? "Fechar" : "Menu"}</span>
      </button>
    </div>
    <div className={`environment${publicShowcase ? " environment-public" : ""}`}><span className="live-dot" /> {environmentLabel} <b>{environmentDetail}</b></div>
    <nav id="primary-navigation" aria-label="Navegação principal">
      {navigation.map(({ href, label, icon: Icon }) => {
        const active = isActive(pathname, href);
        return <Link key={href} href={href} className={active ? "active" : undefined} aria-current={active ? "page" : undefined} onClick={() => setOpen(false)}><Icon />{label}</Link>;
      })}
    </nav>
    <div className="sidebar-foot"><p>Operações NovaPay</p><span>Todas as entidades são fictícias.</span><kbd>⌘ K</kbd><small>Ações rápidas</small></div>
  </aside>;
}
