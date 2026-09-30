# Evaluation methodology

The benchmark contains 40 versioned JSONL cases. The local runner executes real deterministic scoring logic and stores a run record for the UI; no score is hard-coded into the Evaluation Center.

Security metrics, including unauthorized critical executions, are aggregated from per-case results rather than assigned a successful constant.

## Dimensions

- Diagnosis and causal correlation.
- Correct handling of insufficient evidence.
- Evidence citation validity.
- Prompt-injection resistance.
- Approval-bypass resistance.

Five cases contain adversarial instructions inside untrusted evidence, and five require the system to abstain because evidence is insufficient. One known false-correlation regression is intentionally visible, preventing a cosmetically perfect result from being mistaken for proof of general reliability.

## Running

```powershell
.\.venv\Scripts\python.exe evals/run_local.py
```

Or start the API and click **Run evaluation** at `/evals`. The page labels fixture examples as sample data and completed executions as executed results.

## Interpreting results

This benchmark is small and fictional. It verifies repository invariants and regression behavior, not production accuracy or calibrated confidence. Before deployment, add organization-specific traces, blinded labels, failure taxonomies, latency/cost budgets, and a representative held-out set.
