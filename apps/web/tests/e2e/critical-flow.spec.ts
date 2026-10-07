import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const api = "http://127.0.0.1:8000";

async function waitForState(request: APIRequestContext, state: string) {
  await expect.poll(async () => {
    const response = await request.get(`${api}/api/incidents/INC-2026-0042`);
    if (!response.ok()) return "MISSING";
    return (await response.json()).incident.state;
  }, { timeout: 15_000 }).toBe(state);
}

async function expectHeadingBefore(page: Page, first: string, second: string) {
  const firstHeading = page.getByRole("heading", { name: first });
  const secondHeading = page.getByRole("heading", { name: second });
  await expect(firstHeading).toBeVisible();
  await expect(secondHeading).toBeAttached();
  const [firstBox, secondBox] = await Promise.all([
    firstHeading.boundingBox(),
    secondHeading.boundingBox(),
  ]);
  expect(firstBox).not.toBeNull();
  expect(secondBox).not.toBeNull();
  expect(firstBox!.y).toBeLessThan(secondBox!.y);
}

test("flagship incident pauses for approval and resolves only after approval", async ({ page, request }) => {
  await request.post(`${api}/api/demo/reset`);
  await request.post(`${api}/api/chaos/scenarios/payment-webhook-regression/inject`);
  await waitForState(request, "AWAITING_APPROVAL");
  await page.goto("/incidents/INC-2026-0042");
  await expect(page.getByRole("heading", {
    name: "Regressão no esquema do payload do webhook introduzida pela implantação dep_184",
    exact: true,
  })).toBeVisible();
  await expect(page.getByRole("button", { name: "Aprovar reversão exata" })).toBeVisible();
  await expectHeadingBefore(page, "Decisão necessária", "Linha do tempo da investigação");
  await expect(page.getByRole("button", { name: /Marcos \d+/ })).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByText("Executando query_application_logs", { exact: true })).toHaveCount(0);
  await expect(page.getByRole("status")).toContainText("Estado do incidente: aguardando aprovação.");

  const evidence = page.getByRole("button", { name: "Inspecionar evidência TXN-901" });
  await expect(evidence).toHaveAttribute("aria-expanded", "false");
  await evidence.click();
  await expect(evidence).toHaveAttribute("aria-expanded", "true");
  await expect(page.getByRole("heading", { name: "TXN-901" })).toBeFocused();
  await page.getByRole("button", { name: "Fechar evidência" }).click();
  await expect(evidence).toBeFocused();

  await page.getByRole("button", { name: /Ferramentas \d+/ }).click();
  const logActivity = page.locator("details.timeline-activity").filter({ hasText: "query_application_logs" });
  await expect(logActivity).toBeVisible();
  await logActivity.locator("summary").click();
  await expect(logActivity.getByText("tool.started", { exact: true })).toBeVisible();
  await expect(logActivity.getByText("tool.completed", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Política \d+/ }).click();
  await expect(page.getByRole("heading", { name: "Aprovação solicitada" })).toBeVisible();
  await page.getByRole("button", { name: /Marcos \d+/ }).click();

  const beforeApproval = await request.get(`${api}/api/incidents/INC-2026-0042`);
  const waiting = await beforeApproval.json();
  const criticalCall = waiting.tool_calls.find(
    (call: { risk_level: string }) => call.risk_level === "critical_write",
  );
  expect(criticalCall.status).toBe("NOT_EXECUTED");
  expect(waiting.validation).toBeNull();

  const approvalId = waiting.approval.id;
  await page.getByRole("button", { name: "Aprovar reversão exata" }).click();
  await expect(page.getByText("Resolvido", { exact: true }).first()).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByRole("heading", { name: "Os 12 testes do parser passaram e todas as 37 transações pendentes foram recuperadas." })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Relatório do incidente" })).toBeVisible();
  await expectHeadingBefore(page, "Resultado da resolução", "Linha do tempo da investigação");

  const resolvedResponse = await request.get(`${api}/api/incidents/INC-2026-0042`);
  const resolved = await resolvedResponse.json();
  expect(resolved.approval.status).toBe("CONSUMED");
  expect(resolved.validation.passed).toBe(true);
  expect(resolved.report.final_status).toBe("RESOLVED");

  await page.goto("/dashboard");
  await expect(page.getByRole("link", { name: /Pagamentos aprovados continuam pendentes.*Resolvido.*Simulado/ })).toBeVisible();
  await expect(page.getByText("Resolvidos nesta sessão").locator("..").getByText("1", { exact: true })).toBeVisible();
  await expect(page.getByText("Aguardando aprovação", { exact: true })).toHaveCount(0);

  const replay = await request.post(`${api}/api/approvals/${approvalId}/approve`, {
    data: { actor: "replay-attempt" },
  });
  expect(replay.status()).toBe(409);
});

test("rejected critical action escalates without execution", async ({ page, request }) => {
  await request.post(`${api}/api/demo/reset`);
  await request.post(`${api}/api/chaos/scenarios/payment-webhook-regression/inject`);
  await waitForState(request, "AWAITING_APPROVAL");
  await page.goto("/incidents/INC-2026-0042");
  await page.getByRole("button", { name: "Rejeitar reversão" }).click();
  await expect(page.getByText("Escalado", { exact: true })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Decisão: Rejeitada")).toBeVisible();
});

test("approval remains inspectable and keyboard operable at narrow width", async ({
  page,
  request,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await request.post(`${api}/api/demo/reset`);
  await request.post(`${api}/api/chaos/scenarios/payment-webhook-regression/inject`);
  await waitForState(request, "AWAITING_APPROVAL");
  await page.goto("/incidents/INC-2026-0042");

  await expect(page.getByRole("heading", { name: "Decisão necessária" })).toBeInViewport();
  await expectHeadingBefore(page, "Decisão necessária", "Linha do tempo da investigação");

  const approve = page.getByRole("button", { name: "Aprovar reversão exata" });
  await approve.scrollIntoViewIfNeeded();
  await approve.focus();
  await expect(approve).toBeFocused();
  await expect(page.getByText("Escrita crítica", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Menu" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("evaluation center executes the complete deterministic contract", async ({ page }) => {
  await page.goto("/evals", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Executar avaliação" }).click();
  await expect(page.getByText("Resultado executado", { exact: true })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByRole("heading", { name: "40 / 40 casos passaram" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Avaliação concluída. 40 de 40 casos passaram. 0 falhas.");
  await expect(page.getByText("0 falhas", { exact: true })).toBeVisible();
  await expect(page.getByText("eval_false_correlation_020")).toHaveCount(0);
  await expect(
    page
      .getByText("Sucesso do contrato de cenários")
      .locator("..")
      .getByText("100%", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Escritas não autorizadas").locator("..").getByText("0", { exact: true }),
  ).toBeVisible();
  await expect(page.getByText("Sondagens de limite").locator("..").getByText("30", { exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Proveniência da execução" })).toBeVisible();
  await expect(page.getByText("unknown", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Nenhuma execução anterior neste processo.")).toBeVisible();

  await Promise.all([
    page.waitForResponse(response => response.url().endsWith("/api/evals/run") && response.ok()),
    page.getByRole("button", { name: "Executar avaliação" }).click(),
  ]);
  await expect(page.getByText("Resultado anterior").locator("..").getByText("40 / 40 passaram", { exact: true })).toBeVisible();
  await expect(page.getByText("Diferença de aprovações").locator("..").getByText("0 casos", { exact: true })).toBeVisible();
  await page.goto("/dashboard");
  await expect(page.getByText("40/40", { exact: true })).toBeVisible();
  await expect(page.getByText("30 sondagens ativas de limite", { exact: true })).toBeVisible();
});

test("core data surfaces reflow at 320 pixels and retain named table regions", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });

  await page.goto("/dashboard", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "Central de operações" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  await page.goto("/evals", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("status")).toBeAttached();
  await expect(page.getByText("Resultado executado", { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

  await page.goto("/security", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("region", { name: "Invariantes de aprovação" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("forced-colors users retain visible focus and explicit state boundaries", async ({ page }) => {
  await page.emulateMedia({ forcedColors: "active", reducedMotion: "reduce" });
  await page.goto("/security", { waitUntil: "domcontentloaded" });

  const securityLink = page.getByRole("link", { name: "Segurança", exact: true });
  await securityLink.focus();
  await expect(securityLink).toBeFocused();
  expect(await page.evaluate(() => matchMedia("(forced-colors: active)").matches)).toBe(true);
  expect(await securityLink.evaluate(element => getComputedStyle(element).outlineStyle)).not.toBe("none");
  await expect(page.getByText("Vermelho · Escrita crítica")).toBeVisible();
});
