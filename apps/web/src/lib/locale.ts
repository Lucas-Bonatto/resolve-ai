import type { ExecutionStatus, IncidentState, RiskLevel } from "@/types/domain";

const incidentStates: Record<IncidentState, string> = {
  NEW: "Novo",
  TRIAGED: "Triado",
  INVESTIGATING: "Em investigação",
  EVIDENCE_COLLECTED: "Evidências coletadas",
  DIAGNOSING: "Em diagnóstico",
  DIAGNOSED: "Diagnosticado",
  PLAN_PROPOSED: "Plano proposto",
  AWAITING_APPROVAL: "Aguardando aprovação",
  EXECUTING: "Em execução",
  VALIDATING: "Em validação",
  RESOLVED: "Resolvido",
  FAILED: "Falhou",
  ESCALATED: "Escalado",
};

const executionStatuses: Record<ExecutionStatus, string> = {
  EXECUTED: "Executado · EXECUTED",
  SIMULATED: "Simulado · SIMULATED",
  NOT_EXECUTED: "Não executado · NOT_EXECUTED",
  BLOCKED: "Bloqueado · BLOCKED",
};

const statusLabels: Record<string, string> = {
  PENDING: "Pendente",
  APPROVED: "Aprovada",
  REJECTED: "Rejeitada",
  CONSUMED: "Consumida",
  EXPIRED: "Expirada",
  RUNNING: "Em execução",
  COMPLETED: "Concluída",
  FAILED: "Falhou",
  CONFIRMED: "Confirmada",
  WEAKENED: "Enfraquecida",
  ACTIVE: "Ativa",
  SUPPORTED_ROOT_CAUSE: "Causa raiz sustentada",
  INSUFFICIENT_EVIDENCE: "Evidência insuficiente",
  RESOLVED: "Resolvido",
  ESCALATED: "Escalado",
};

const riskLabels: Record<RiskLevel, string> = {
  read: "Leitura",
  safe_write: "Escrita segura",
  critical_write: "Escrita crítica",
};

const sourceLabels: Record<string, string> = {
  TRANSACTION: "TRX",
  SERVICE_METRIC: "MÉTR",
  LOG: "LOG",
  DEPLOYMENT: "DEP",
  TEST_RESULT: "TESTE",
};

const demoText: Record<string, string> = {
  "Approved payments remain pending": "Pagamentos aprovados continuam pendentes",
  "NovaPay customers report successful payments remaining in pending state.": "Clientes da NovaPay relatam pagamentos bem-sucedidos que permanecem no estado pendente.",
  "Incident detected": "Incidente detectado",
  "Monitoring detected 37 approved payments still pending.": "O monitoramento detectou 37 pagamentos aprovados ainda pendentes.",
  "Incident triaged": "Incidente triado",
  "Severity confirmed as SEV-1.": "Severidade confirmada como SEV-1.",
  "Investigation started": "Investigação iniciada",
  "Incident Coordinator started an evidence-first run.": "O Coordenador de Incidentes iniciou uma execução orientada por evidências.",
  "Validated tool call started.": "A chamada de ferramenta validada foi iniciada.",
  "Affected transactions identified": "Transações afetadas identificadas",
  "37 correlated transactions added as evidence.": "37 transações correlacionadas foram adicionadas como evidência.",
  "Provider outage hypothesis weakened": "Hipótese de indisponibilidade do provedor enfraquecida",
  "Provider health is normal; confidence reduced to low.": "A saúde do provedor está normal; a confiança foi reduzida para baixa.",
  "Error pattern identified": "Padrão de erro identificado",
  "Schema validation errors began inside the deployment window.": "Os erros de validação de esquema começaram dentro da janela de implantação.",
  "Webhook regression hypothesis": "Hipótese de regressão no webhook",
  "Deployment and log timing support a parser regression.": "A implantação e os horários dos logs sustentam uma regressão no parser.",
  "Regression hypothesis confirmed": "Hipótese de regressão confirmada",
  "Controlled test and source evidence support the regression.": "O teste controlado e as evidências de código sustentam a regressão.",
  "Evidence collection complete": "Coleta de evidências concluída",
  "Generating diagnosis": "Gerando diagnóstico",
  "Provider is producing a typed diagnosis from validated evidence.": "O provedor está produzindo um diagnóstico tipado a partir de evidências validadas.",
  "Root cause identified": "Causa raiz identificada",
  "Webhook payload schema regression introduced by deployment dep_184": "Regressão no esquema do payload do webhook introduzida pela implantação dep_184",
  "Remediation plan proposed": "Plano de remediação proposto",
  "Rollback dep_184, restore the compatible parser, then replay and validate affected events.": "Reverter a dep_184, restaurar o parser compatível e então reprocessar e validar os eventos afetados.",
  "Human approval required": "Aprovação humana necessária",
  "Approval requested": "Aprovação solicitada",
  "Critical rollback is paused pending an operator decision.": "A reversão crítica está pausada aguardando a decisão de um operador.",
  "Affected transaction sample": "Amostra de transações afetadas",
  "37 transactions are approved by the provider but pending in NovaPay.": "37 transações foram aprovadas pelo provedor, mas continuam pendentes na NovaPay.",
  "Provider health normal": "Saúde do provedor normal",
  "The payment provider reports normal health during the incident window.": "O provedor de pagamentos apresenta saúde normal durante a janela do incidente.",
  "Webhook schema validation failure": "Falha de validação do esquema do webhook",
  "ValidationError: field paymentStatus not permitted": "ValidationError: campo paymentStatus não permitido",
  "Failure window correlation": "Correlação da janela de falha",
  "Validation failures began inside the deployment window.": "As falhas de validação começaram dentro da janela de implantação.",
  "Webhook worker deployment dep_184": "Implantação dep_184 do webhook worker",
  "Deployment dep_184 changed the parser four minutes before failures began.": "A implantação dep_184 alterou o parser quatro minutos antes do início das falhas.",
  "Regression reproduced": "Regressão reproduzida",
  "The controlled legacy payload fails on dep_184 and passes on dep_183.": "O payload legado controlado falha na dep_184 e passa na dep_183.",
  "Payment provider outage": "Indisponibilidade do provedor de pagamentos",
  "The external provider may not be confirming payments.": "O provedor externo pode não estar confirmando os pagamentos.",
  "Compare provider health and transaction receipts.": "Comparar a saúde do provedor e os comprovantes das transações.",
  "Webhook schema regression": "Regressão no esquema do webhook",
  "Deployment dep_184 removed compatibility for the provider's paymentStatus field.": "A implantação dep_184 removeu a compatibilidade com o campo paymentStatus do provedor.",
  "Run the legacy payload regression fixture.": "Executar a fixture de regressão do payload legado.",
  "Database persistence failure": "Falha de persistência no banco de dados",
  "NovaPay may have failed to persist provider confirmations.": "A NovaPay pode não ter persistido as confirmações do provedor.",
  "Compare stored state with parser acceptance results.": "Comparar o estado armazenado com os resultados de aceitação do parser.",
  "Deployment configuration mismatch": "Incompatibilidade de configuração da implantação",
  "A runtime flag may have changed webhook compatibility.": "Uma flag de execução pode ter alterado a compatibilidade do webhook.",
  "Compare dep_183 and dep_184 parser behavior.": "Comparar o comportamento do parser nas versões dep_183 e dep_184.",
  "The webhook worker rejected approved-payment events after deployment dep_184.": "O webhook worker rejeitou eventos de pagamentos aprovados após a implantação dep_184.",
  "Rollback dep_184, deploy the compatible parser, and replay the affected events.": "Reverter a dep_184, implantar o parser compatível e reprocessar os eventos afetados.",
  "Rollback webhook worker": "Reverter o webhook worker",
  "Restore dep_183.": "Restaurar a dep_183.",
  "Validate event processing": "Validar o processamento de eventos",
  "Run regression and recovery checks.": "Executar verificações de regressão e recuperação.",
  "If validation fails, keep dep_183 active and escalate to the payments team.": "Se a validação falhar, manter a dep_183 ativa e escalar para a equipe de pagamentos.",
  "Run 12 parser tests and verify all 37 pending transactions recover.": "Executar 12 testes do parser e verificar a recuperação das 37 transações pendentes.",
  "Rollback webhook-worker to dep_183": "Reverter webhook-worker para dep_183",
  "Failures began after dep_184 and the regression test reproduces the parser defect.": "As falhas começaram após a dep_184 e o teste de regressão reproduz o defeito do parser.",
  "A brief webhook processing interruption while the worker restarts.": "Uma breve interrupção no processamento de webhooks enquanto o worker reinicia.",
  "Rollback approved": "Reversão aprovada",
  "Executing approved remediation": "Executando remediação aprovada",
  "The argument-bound rollback is now executing.": "A reversão vinculada aos argumentos está sendo executada.",
  "Rollback completed": "Reversão concluída",
  "webhook-worker now runs dep_183.": "O webhook-worker agora executa a dep_183.",
  "Validating outcome": "Validando resultado",
  "Regression and transaction recovery checks are running.": "As verificações de regressão e recuperação das transações estão em execução.",
  "Validation passed": "Validação aprovada",
  "12 parser tests passed and all 37 pending transactions recovered.": "Os 12 testes do parser passaram e todas as 37 transações pendentes foram recuperadas.",
  "Incident resolved": "Incidente resolvido",
  "Rollback succeeded and the recovery was verified.": "A reversão foi concluída e a recuperação foi verificada.",
  "Evidence-backed investigation completed with validated recovery.": "A investigação sustentada por evidências foi concluída com recuperação validada.",
  "Deterministic grader: root-cause contract mismatch.": "Avaliador determinístico: divergência no contrato de causa raiz.",
};

export function incidentStateLabel(value: IncidentState | string): string {
  return incidentStates[value as IncidentState] ?? value;
}

export function executionStatusLabel(value: ExecutionStatus | string): string {
  return executionStatuses[value as ExecutionStatus] ?? value;
}

export function statusLabel(value: string): string {
  return statusLabels[value] ?? incidentStateLabel(value);
}

export function riskLevelLabel(value: RiskLevel | string): string {
  return riskLabels[value as RiskLevel] ?? value;
}

export function sourceTypeLabel(value: string): string {
  return sourceLabels[value] ?? value.slice(0, 4);
}

export function translateDemoText(value: string): string {
  const exact = demoText[value];
  if (exact) return exact;
  if (value.startsWith("Running ")) return `Executando ${value.slice("Running ".length)}`;
  if (value.endsWith(" completed")) return `Concluído: ${value.slice(0, -" completed".length)}`;
  if (value.startsWith("Structured result returned")) return value.replace("Structured result returned", "Resultado estruturado retornado");
  if (/^\d+ evidence records support or challenge the hypotheses\.$/.test(value)) {
    return value.replace(" evidence records support or challenge the hypotheses.", " registros de evidência sustentam ou contestam as hipóteses.");
  }
  if (value.endsWith(" approved the exact requested action.")) {
    return value.replace(" approved the exact requested action.", " aprovou a ação exata solicitada.");
  }
  return value;
}

export function formatPtDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}
