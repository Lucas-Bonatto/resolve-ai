# ADR 0003: Server-Sent Events for incident updates

Status: accepted.

ResolveAI needs server-to-browser progress events and ordinary client-to-server commands. SSE is simpler to operate, reconnect, inspect, and secure than a bidirectional socket for this shape. Event IDs support browser reconciliation; REST endpoints remain idempotent command boundaries.
