from __future__ import annotations

import json
import logging
from contextvars import ContextVar, Token
from typing import Any

from app.domain.models import new_id

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)
logger = logging.getLogger("resolveai")


def current_correlation_id() -> str:
    return _correlation_id.get() or new_id("corr")


def set_correlation_id(value: str) -> Token[str | None]:
    return _correlation_id.set(value)


def reset_correlation_id(token: Token[str | None]) -> None:
    _correlation_id.reset(token)


def log_event(event: str, **fields: Any) -> None:
    """Emit bounded structured metadata; callers must never pass raw payloads or secrets."""
    payload = {"event": event, "correlation_id": current_correlation_id(), **fields}
    logger.info(json.dumps(payload, sort_keys=True, default=str))
