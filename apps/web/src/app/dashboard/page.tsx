import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { SparkIcon } from "@/components/icons";
import { DashboardOverview } from "@/features/dashboard/dashboard-overview";

export const metadata = { title: "Central de operações" };

export default function DashboardPage() {
  return <AppShell title="Central de operações" description="Estado ao vivo da API local de demonstração; áreas com dados de exemplo estão identificadas." actions={<Link className="button button-primary" href="/incidents/INC-2026-0042"><SparkIcon /> Abrir cenário principal</Link>}>
    <DashboardOverview />
  </AppShell>;
}
