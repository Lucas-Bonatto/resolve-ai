# Security policy

ResolveAI is a fictional operations simulation, but security reports about the code are taken seriously.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub's private security advisory flow after the repository is published. Include the affected component, reproduction steps, likely impact, and any suggested mitigation. Do not include real credentials or customer data.

Until a public repository security channel exists, keep the report private and contact the repository owner directly.

## Scope

The latest default branch is supported. Particularly relevant findings include approval bypass, cross-incident evidence access, prompt-injection control flow, unsafe tool argument handling, replay, secret disclosure, and misleading execution labels.

## Demo boundary

The local demo has no authentication and uses in-memory state. Do not expose it directly to an untrusted network. A hosted deployment needs identity, tenant isolation, durable storage, rate limits, CSRF/origin controls, and an operational secret manager before it can be considered production-ready.
