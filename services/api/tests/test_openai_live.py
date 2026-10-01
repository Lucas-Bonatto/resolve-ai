import os

import pytest

from app.agents.providers import OpenAIProvider
from app.domain.enums import EvidenceType
from app.domain.models import Diagnosis, Evidence


@pytest.mark.asyncio
@pytest.mark.live
async def test_openai_provider_returns_the_typed_diagnosis_contract() -> None:
    if os.getenv("RUN_OPENAI_LIVE_SMOKE") != "1":
        pytest.skip("Set RUN_OPENAI_LIVE_SMOKE=1 for an explicitly authorized paid smoke test")

    evidence = [
        Evidence(
            id="LIVE-EVIDENCE-1",
            incident_id="INC-LIVE-SMOKE",
            source_type=EvidenceType.LOG,
            source_reference="fictional-live-smoke",
            title="Fictional parser error",
            summary="The fictional parser rejected a paymentStatus field after deployment.",
            relevance=0.8,
            correlation_id="corr_live_smoke",
        )
    ]
    diagnosis = await OpenAIProvider().diagnose(
        "Fictional NovaPay webhook events remain pending.", evidence
    )

    assert isinstance(diagnosis, Diagnosis)
    assert set(diagnosis.evidence_ids).issubset({item.id for item in evidence})

