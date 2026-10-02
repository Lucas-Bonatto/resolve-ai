import Link from "next/link";
import { AppShell } from "@/components/app-shell";
import { SparkIcon } from "@/components/icons";
import { DashboardOverview } from "@/features/dashboard/dashboard-overview";

export const metadata = { title: "Command center" };

export default function DashboardPage() {
  return <AppShell title="Command center" description="Live state from the local demo API; fixture-only sections are explicitly labeled." actions={<Link className="button button-primary" href="/incidents/INC-2026-0042"><SparkIcon /> Open flagship</Link>}>
    <DashboardOverview />
  </AppShell>;
}
