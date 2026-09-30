import { AppShell } from "@/components/app-shell";
import { EvaluationCenter } from "@/features/evaluations/evaluation-center";

export const metadata = { title: "Evaluation center" };

export default function EvaluationsPage() {
  return <AppShell title="Evaluation center" description="Measure diagnosis, evidence use, tool behavior, and security invariants."><EvaluationCenter /></AppShell>;
}
