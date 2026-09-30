# Demo script

The flagship demo takes roughly two minutes and is safe to repeat.

1. Open the landing page and call out the fictional NovaPay disclaimer.
2. Enter the command center and open incident `INC-2026-0042`.
3. Inject **Payment webhook regression**. The real coordinator emits live events while deterministic tools collect transactions, metrics, logs, deployment history, and a controlled reproduction test.
4. Inspect the competing hypotheses and evidence-linked diagnosis.
5. At `AWAITING_APPROVAL`, review the exact rollback arguments and evidence references.
6. Choose one path:
   - **Approve**: the simulated rollback executes, a post-remediation check becomes new evidence, and only then does the incident resolve.
   - **Reject**: the incident escalates and the audit log records `NOT_EXECUTED`.
7. Open the Evaluation Center, run the 40-case benchmark, and inspect the intentionally visible failing regression.
8. Open Security and Audit to show that policy decisions and operator actions are product objects, not hidden model behavior.

Reset through `POST /api/demo/reset` or the reset action in the app before another run.
