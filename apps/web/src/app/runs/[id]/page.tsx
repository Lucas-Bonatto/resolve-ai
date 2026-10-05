import { AppShell } from "@/components/app-shell";
import { RunDetail } from "@/features/runs/run-detail";

export const metadata = { title: "Execução do agente" };

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <AppShell title="Execução do agente" description="Provedor, rastreamento, limites, uso e resultado da execução sem raciocínio privado."><RunDetail runId={id} /></AppShell>;
}
