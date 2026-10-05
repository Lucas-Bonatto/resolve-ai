import pytest

from app.agents.providers import DemoAIProvider, OpenAIProvider, configured_provider
from app.config import Settings, settings
from app.domain.errors import AIProviderUnavailable


def test_demo_provider_is_the_safe_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "demo")
    assert isinstance(configured_provider(), DemoAIProvider)


def test_real_provider_requires_explicit_enable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "openai")
    monkeypatch.setattr(settings, "enable_real_ai", False)
    with pytest.raises(AIProviderUnavailable, match="ENABLE_REAL_AI"):
        configured_provider()

    monkeypatch.setattr(settings, "enable_real_ai", True)
    assert isinstance(configured_provider(), OpenAIProvider)


def test_unknown_provider_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ai_provider", "untrusted-provider")
    with pytest.raises(AIProviderUnavailable, match="Unsupported"):
        configured_provider()


def test_openai_key_is_held_as_a_secret() -> None:
    isolated = Settings(_env_file=None, openai_api_key="test-secret-value")
    assert isolated.openai_api_key is not None
    assert "test-secret-value" not in str(isolated.openai_api_key)
    assert "test-secret-value" not in repr(isolated)


def test_documented_code_revision_environment_is_loaded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("RESOLVEAI_CODE_REVISION", "84686f4308ec")

    isolated = Settings(_env_file=None)

    assert isolated.code_revision == "84686f4308ec"
