# ADR 0001: App-owned manager agent runtime

Status: accepted.

ResolveAI uses one Incident Coordinator that invokes bounded domain tools and optional specialist analysis. The OpenAI Agents SDK runs inside FastAPI; it does not own authorization or persistence. This matches the product's need for deterministic approvals, evidence validation, and replayable demo behavior. A multi-agent swarm was rejected because it adds latency and obscures responsibility without improving this workflow.
