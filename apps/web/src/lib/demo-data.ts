export const services = [
  { name: "payment-api", status: "Healthy", latency: "84 ms" },
  { name: "transaction-service", status: "Healthy", latency: "62 ms" },
  { name: "webhook-worker", status: "Degraded", latency: "142 errors" },
  { name: "customer-service", status: "Healthy", latency: "48 ms" },
  { name: "auth-service", status: "Healthy", latency: "39 ms" },
];

export const incidentFixtures = [
  { id: "INC-2026-0042", title: "Approved payments remain pending", severity: "SEV-1", status: "Awaiting demo", service: "webhook-worker", impact: "37 transactions", age: "Flagship" },
  { id: "INC-2026-0038", title: "Authentication failure spike", severity: "SEV-2", status: "Resolved", service: "auth-service", impact: "128 sessions", age: "2d ago" },
  { id: "INC-2026-0031", title: "Queue processing latency", severity: "SEV-2", status: "Resolved", service: "notification-service", impact: "4,108 messages", age: "6d ago" },
  { id: "INC-2026-0027", title: "Provider regional timeout", severity: "SEV-3", status: "Escalated", service: "payment-api", impact: "11 requests", age: "9d ago" },
];
