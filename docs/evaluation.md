# Evaluation methodology

The benchmark contains 40 versioned JSONL cases in `evals/cases/benchmark.jsonl`. The local `EvaluationRunner` applies deterministic mappings and graders and stores a run record for the UI; it does not call either AI provider. Generated runs are labeled `provider=demo`, `model=deterministic-demo-v1`, and `run_kind=deterministic-contract`, with suite and code-revision metadata. No score is hard-coded into the Evaluation Center.

`scenario_contract_success_rate` is `passed cases / executed cases`. The historical 97.5% is therefore 39/40, not model accuracy. The failing case is `eval_false_correlation_020`: its `false_correlation` signal is deliberately not mapped to the expected provider-outage cause, so the deterministic grader reports a root-cause contract mismatch. It remains visible as a regression.

Security metrics, including approval bypasses, prompt-injection bypasses, evidence-integrity violations, and unauthorized critical executions, are aggregated from per-case results rather than assigned a successful constant. A negative unit test injects a violating case and proves the aggregate becomes nonzero.

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

The result is deterministic in decisions and aggregate scores for a fixed case file and code revision; IDs, timestamps, and measured millisecond durations can change between runs. This benchmark is small and fictional. It verifies scenario contracts and grader behavior, not OpenAI model quality, production accuracy, or calibrated confidence. Before deployment, add organization-specific traces, blinded labels, failure taxonomies, latency/cost budgets, and a representative held-out set.
