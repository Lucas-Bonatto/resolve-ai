from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings, settings
from app.domain.errors import ReadOnlyRuntimeError


@dataclass(frozen=True)
class RuntimeCapabilities:
    deployment_profile: str
    interactive: bool
    mutations_allowed: bool
    real_ai_enabled: bool
    fictional_data: bool = True


class RuntimePolicy:
    """Server-owned deployment capabilities; browser state never grants authority."""

    def __init__(self, runtime_settings: Settings = settings) -> None:
        self.settings = runtime_settings

    @property
    def is_public_showcase(self) -> bool:
        return self.settings.deployment_profile == "public_showcase"

    def capabilities(self) -> RuntimeCapabilities:
        interactive = not self.is_public_showcase
        return RuntimeCapabilities(
            deployment_profile=self.settings.deployment_profile,
            interactive=interactive,
            mutations_allowed=interactive,
            real_ai_enabled=(
                self.settings.ai_provider == "openai" and self.settings.enable_real_ai
            ),
        )

    def require_mutations(self) -> None:
        if self.is_public_showcase:
            raise ReadOnlyRuntimeError(
                "A vitrine pública é somente leitura; mutações estão desabilitadas no backend."
            )


runtime_policy = RuntimePolicy()
