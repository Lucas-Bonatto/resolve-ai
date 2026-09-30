# ADR 0002: Deterministic server-side permissions

Status: accepted.

Each tool has a fixed risk level: read, safe write, or critical write. `PermissionEngine` returns allow, require approval, or deny. Critical execution requires a valid approval bound to the exact canonical arguments. Prompt instructions and model output are never authorization inputs.
