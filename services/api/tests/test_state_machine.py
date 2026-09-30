import pytest

from app.domain.enums import IncidentState
from app.domain.errors import InvalidStateTransition
from app.domain.state_machine import validate_transition


def test_valid_transition() -> None:
    validate_transition(IncidentState.NEW, IncidentState.TRIAGED)


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(InvalidStateTransition):
        validate_transition(IncidentState.NEW, IncidentState.RESOLVED)
