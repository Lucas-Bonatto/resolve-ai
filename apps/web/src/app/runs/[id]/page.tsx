import { AppShell } from "@/components/app-shell";
import { RunDetail } from "@/features/runs/run-detail";

export const metadata = { title: "Agent run" };

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell title="Agent run" description="Provider, trace, bounds, usage, and execution outcome without private reasoning."><RunDetail runId={id} /></AppShell>;
}
