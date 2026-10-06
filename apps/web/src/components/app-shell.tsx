import type { ReactNode } from "react";
import { AppNavigation } from "./app-navigation";

export function AppShell({ children, title, description, actions }: { children: ReactNode; title: string; description: string; actions?: ReactNode }) {
  return <div className="app-layout">
    <a className="skip-link" href="#main-content">Pular para o conteúdo principal</a>
    <AppNavigation />
    <main className="app-main" id="main-content" tabIndex={-1}>
      <header className="app-header"><div><p className="breadcrumb">NovaPay / Operações</p><h1>{title}</h1><p>{description}</p></div>{actions && <div className="header-actions">{actions}</div>}</header>
      {children}
    </main>
  </div>;
}
