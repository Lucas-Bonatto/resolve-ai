from .enums import IncidentState
from .errors import InvalidStateTransition

ALLOWED_TRANSITIONS: dict[IncidentState, frozenset[IncidentState]] = {
    IncidentState.NEW: frozenset({IncidentState.TRIAGED, IncidentState.FAILED}),
    IncidentState.TRIAGED: frozenset(
        {IncidentState.INVESTIGATING, IncidentState.ESCALATED, IncidentState.FAILED}
    ),
    IncidentState.INVESTIGATING: frozenset(
        {IncidentState.EVIDENCE_COLLECTED, IncidentState.FAILED, IncidentState.ESCALATED}
    ),
    IncidentState.EVIDENCE_COLLECTED: frozenset(
        {IncidentState.DIAGNOSING, IncidentState.ESCALATED, IncidentState.FAILED}
    ),
    IncidentState.DIAGNOSING: frozenset(
        {IncidentState.DIAGNOSED, IncidentState.ESCALATED, IncidentState.FAILED}
    ),
    IncidentState.DIAGNOSED: frozenset(
        {IncidentState.PLAN_PROPOSED, IncidentState.ESCALATED, IncidentState.FAILED}
    ),
    IncidentState.PLAN_PROPOSED: frozenset(
        {
            IncidentState.AWAITING_APPROVAL,
            IncidentState.EXECUTING,
            IncidentState.ESCALATED,
            IncidentState.FAILED,
        }
    ),
    IncidentState.AWAITING_APPROVAL: frozenset(
        {IncidentState.EXECUTING, IncidentState.ESCALATED, IncidentState.FAILED}
    ),
    IncidentState.EXECUTING: frozenset({IncidentState.VALIDATING, IncidentState.FAILED}),
    IncidentState.VALIDATING: frozenset(
        {IncidentState.RESOLVED, IncidentState.FAILED, IncidentState.ESCALATED}
    ),
    IncidentState.RESOLVED: frozenset(),
    IncidentState.FAILED: frozenset(),
    IncidentState.ESCALATED: frozenset(),
}


def validate_transition(current: IncidentState, target: IncidentState) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(f"Cannot transition incident from {current} to {target}")
