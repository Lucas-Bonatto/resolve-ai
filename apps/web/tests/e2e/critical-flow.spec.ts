import { expect, test, type APIRequestContext } from "@playwright/test";

const api = "http://127.0.0.1:8000";

async function waitForState(request: APIRequestContext, state: string) {
  await expect.poll(async () => {
    const response = await request.get(`${api}/api/incidents/INC-2026-0042`);
    if (!response.ok()) return "MISSING";
    return (await response.json()).incident.state;
  }, { timeout: 15_000 }).toBe(state);
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
  await expect(page.getByRole("button", { name: "Approve" })).toBeVisible();
  await page.getByRole("button", { name: "Approve" }).click();
  await expect(page.getByText("RESOLVED", { exact: true })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Post-remediation validation passed")).toBeVisible();
});

test("rejected critical action escalates without execution", async ({ page, request }) => {
  await request.post(`${api}/api/demo/reset`);
  await request.post(`${api}/api/chaos/scenarios/payment-webhook-regression/inject`);
  await waitForState(request, "AWAITING_APPROVAL");
  await page.goto("/incidents/INC-2026-0042");
  await page.getByRole("button", { name: "Reject" }).click();
  await expect(page.getByText("ESCALATED", { exact: true })).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Decision: REJECTED")).toBeVisible();
});

test("evaluation center executes and exposes the known regression", async ({ page }) => {
  await page.goto("/evals", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Run evaluation" }).click();
  await expect(page.getByText("Executed result")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("eval_false_correlation_020")).toBeVisible();
  await expect(page.getByText("0%", { exact: true }).first()).toBeVisible();
});
