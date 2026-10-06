import { AppShell } from "@/components/app-shell";
import { EvaluationCenter } from "@/features/evaluations/evaluation-center";

export const metadata = { title: "Central de avaliações" };

export default function EvaluationsPage() {
  return <AppShell title="Central de avaliações" description="Meça diagnóstico, uso de evidências, comportamento das ferramentas e invariantes de segurança."><EvaluationCenter /></AppShell>;
}
