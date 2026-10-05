import { AppShell } from "@/components/app-shell";
import { IncidentTable } from "@/features/incidents/incident-table";

export const metadata = { title: "Incidentes" };

export default function IncidentsPage() {
  return <AppShell title="Incidentes" description="Pesquise, filtre e inspecione as investigações operacionais da NovaPay."><IncidentTable /></AppShell>;
}
