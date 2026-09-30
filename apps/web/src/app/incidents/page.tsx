import { AppShell } from "@/components/app-shell";
import { IncidentTable } from "@/features/incidents/incident-table";

export const metadata = { title: "Incidents" };

export default function IncidentsPage() {
  return <AppShell title="Incidents" description="Search, filter, and inspect NovaPay operational investigations."><IncidentTable /></AppShell>;
}
