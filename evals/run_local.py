import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.application.evaluation import EvaluationRunner, serialize_run
from app.application.store import repository


def main() -> None:
    run = EvaluationRunner(repository).run()
    output = ROOT / "evals" / "results" / "latest.json"
    output.write_text(serialize_run(run), encoding="utf-8")
    print(f"EXECUTED {len(run.results)} evaluation cases -> {output}")
    if run.metrics["unauthorized_critical_tool_execution"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
