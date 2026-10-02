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
    name: "Webhook payload schema regression introduced by deployment dep_184",
    exact: true,
  })).toBeVisible();
  await expect(page.getByRole("button", { name: "Approve exact rollback" })).toBeVisible();
  await expectHeadingBefore(page, "Decision required", "Investigation timeline");

  const beforeApproval = await request.get(`${api}/api/incidents/INC-2026-0042`);
  const waiting = await beforeApproval.json();
  const criticalCall = waiting.tool_calls.find(
    (call: { risk_level: string }) => call.risk_level === "critical_write",
  );
  expect(criticalCall.status).toBe("NOT_EXECUTED");
  expect(waiting.validation).toBeNull();

  const approvalId = waiting.approval.id;
  await page.getByRole("button", { name: "Approve exact rollback" }).click();
  await expect(page.getByText("RESOLVED", { exact: true }).first()).toBeVisible({
    timeout: 10_000,
  });
  await expect(page.getByText("Post-remediation validation passed")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Incident report" })).toBeVisible();
  await expectHeadingBefore(page, "Resolution outcome", "Investigation timeline");

  const resolvedResponse = await request.get(`${api}/api/incidents/INC-2026-0042`);
  const resolved = await resolvedResponse.json();
  expect(resolved.approval.status).toBe("CONSUMED");
  expect(resolved.validation.passed).toBe(true);
  expect(resolved.report.final_status).toBe("RESOLVED");

  await page.goto("/dashboard");
  await expect(page.getByRole("link", { name: /Approved payments remain pending.*Resolved SIMULATED/ })).toBeVisible();
  await expect(page.getByText("Resolved this session").locator("..").getByText("1", { exact: true })).toBeVisible();
  await expect(page.getByText("1 awaiting demo launch")).toHaveCount(0);

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
  await page.getByRole("button", { name: "Reject rollback" }).click();
  await expect(page.getByText("ESCALATED", { exact: true })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Decision: REJECTED")).toBeVisible();
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

  await expect(page.getByRole("heading", { name: "Decision required" })).toBeInViewport();
  await expectHeadingBefore(page, "Decision required", "Investigation timeline");

  const approve = page.getByRole("button", { name: "Approve exact rollback" });
  await approve.scrollIntoViewIfNeeded();
  await approve.focus();
  await expect(approve).toBeFocused();
  await expect(page.getByText("Critical write", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Menu" })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test("evaluation center executes and exposes the known regression", async ({ page }) => {
  await page.goto("/evals", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Run evaluation" }).click();
  await expect(page.getByText("Executed result")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("eval_false_correlation_020")).toBeVisible();
  await expect(
    page
      .getByText("Scenario contract success")
      .locator("..")
      .getByText("97.5%", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Unauthorized writes").locator("..").getByText("0", { exact: true }),
  ).toBeVisible();
  await page.goto("/dashboard");
  await expect(page.getByText("39/40", { exact: true })).toBeVisible();
  await expect(page.getByText("30 active boundary probes", { exact: true })).toBeVisible();
});
