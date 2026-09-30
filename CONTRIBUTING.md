# Contributing

Thank you for improving ResolveAI. Keep changes small, typed, testable, and explicit about what is simulated.

## Development workflow

1. Open an issue that states the user impact and trust-boundary implications.
2. Create a focused branch from the default branch.
3. Add or update tests before changing state transitions, evidence rules, or permissions.
4. Run the checks documented in the README.
5. Open a pull request using the repository template and include screenshots for UI changes.

## Invariants

- A model response never grants its own permission.
- Critical writes require an unexpired approval for the exact incident, tool call, and arguments.
- Diagnoses reference incident-owned evidence.
- Untrusted tool output and customer text remain data, not instructions.
- UI and documentation never present simulated behavior as production execution.
- Secrets, access tokens, private reasoning, and real customer data are never committed or logged.

By participating, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
