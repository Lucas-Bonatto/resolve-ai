export const services = [
  { name: "payment-api", status: "Saudável", latency: "84 ms" },
  { name: "transaction-service", status: "Saudável", latency: "62 ms" },
  { name: "webhook-worker", status: "Degradado", latency: "142 erros" },
  { name: "customer-service", status: "Saudável", latency: "48 ms" },
  { name: "auth-service", status: "Saudável", latency: "39 ms" },
];

export const incidentFixtures = [
  { id: "INC-2026-0042", title: "Pagamentos aprovados continuam pendentes", severity: "SEV-1", status: "Aguardando demonstração", service: "webhook-worker", impact: "37 transações", age: "Cenário principal" },
  { id: "INC-2026-0038", title: "Pico de falhas de autenticação", severity: "SEV-2", status: "Resolvido", service: "auth-service", impact: "128 sessões", age: "há 2 dias" },
  { id: "INC-2026-0031", title: "Latência no processamento da fila", severity: "SEV-2", status: "Resolvido", service: "notification-service", impact: "4.108 mensagens", age: "há 6 dias" },
  { id: "INC-2026-0027", title: "Timeout regional do provedor", severity: "SEV-3", status: "Escalado", service: "payment-api", impact: "11 solicitações", age: "há 9 dias" },
];
