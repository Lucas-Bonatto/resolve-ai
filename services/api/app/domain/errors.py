class ResolveAIError(Exception):
    """Base class for typed domain failures."""


class IncidentNotFound(ResolveAIError):
    pass


class InvalidStateTransition(ResolveAIError):
    pass


class ApprovalInvalid(ResolveAIError):
    pass


class AIProviderUnavailable(ResolveAIError):
    pass


class ToolExecutionFailed(ResolveAIError):
    pass


class EvaluationFailed(ResolveAIError):
    pass


class EvidenceIntegrityError(ResolveAIError):
    pass


class PersistenceError(ResolveAIError):
    pass


class ReadOnlyRuntimeError(ResolveAIError):
    pass
