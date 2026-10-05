import { AppShell } from "@/components/app-shell";
import { WarRoom } from "@/features/war-room/war-room";

export const metadata = { title: "Sala de crise do incidente" };

export default async function IncidentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell title="Sala de crise do incidente" description="Evidências, hipóteses, ferramentas e aprovações em uma única visão operacional."><WarRoom incidentId={id} /></AppShell>;
}
