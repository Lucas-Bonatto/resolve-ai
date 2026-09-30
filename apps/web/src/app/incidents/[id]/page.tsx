import { AppShell } from "@/components/app-shell";
import { WarRoom } from "@/features/war-room/war-room";

export const metadata = { title: "Incident war room" };

export default async function IncidentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell title="Incident war room" description="Evidence, hypotheses, tools, and approvals in one operational view."><WarRoom incidentId={id} /></AppShell>;
}
