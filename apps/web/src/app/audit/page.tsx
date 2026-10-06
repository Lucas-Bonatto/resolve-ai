import { AppShell } from "@/components/app-shell";
import { AuditLog } from "@/features/audit/audit-log";

export const metadata = { title: "Registro de auditoria" };

export default function AuditPage() {
  return <AppShell title="Registro de auditoria" description="Registros somente anexáveis do fluxo, das políticas, das ferramentas e das decisões humanas."><AuditLog /></AppShell>;
}
