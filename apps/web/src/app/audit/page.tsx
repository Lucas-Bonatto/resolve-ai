import { AppShell } from "@/components/app-shell";
import { AuditLog } from "@/features/audit/audit-log";

export const metadata = { title: "Audit log" };

export default function AuditPage() {
  return <AppShell title="Audit log" description="Append-only records for workflow, policy, tools, and human decisions."><AuditLog /></AppShell>;
}
