"""Controlled buggy fixture used only by the code-incident scenario."""


def parse_payment_event(payload: dict[str, object]) -> str:
    # Scenario bug: dep_184 only accepts the new snake_case field and rejects
    # the provider's still-supported camelCase alias.
    status = payload.get("payment_status")
    if not isinstance(status, str):
        raise ValueError("field paymentStatus not permitted")
    return status
