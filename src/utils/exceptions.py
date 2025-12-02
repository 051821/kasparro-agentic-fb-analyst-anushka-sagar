# src/utils/exceptions.py
class AgentError(Exception):
    """Base class for agent errors."""

class DataValidationError(AgentError):
    """Raised when dataset fails validation or schema checks."""

class DriftDetectedWarning(AgentError):
    """Non-fatal warning used to mark drift."""

class LLMError(AgentError):
    """Raised when LLM calls fail repeatedly."""

class RetryLimitError(AgentError):
    """Raised when retry attempts are exhausted."""
