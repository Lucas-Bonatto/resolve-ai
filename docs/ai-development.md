# AI-assisted development disclosure

ResolveAI was built with AI-assisted research, implementation, and review. The human operator selected the product direction and authorized local setup; Codex inspected current official documentation, created the implementation, and ran the verification suite.

AI assistance does not replace repository evidence. Claims in the UI and README are grounded in source code, executable tests, generated evaluation results, or explicit simulation labels. The project does not store or expose private model reasoning.

The OpenAI API key used for optional local-provider verification is stored only in ignored local configuration. It is not included in source, tests, screenshots, or documentation.

## Reproducibility standard

- Research sources are linked from the implementation plan.
- Architectural choices with meaningful alternatives have ADRs.
- Security properties have negative tests.
- Browser journeys exercise the real local API rather than mocked UI responses.
- Known limitations and the visible evaluation regression are retained.
