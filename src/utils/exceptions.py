"""Custom exceptions for PR Agent."""


class PRAgentError(Exception):
    """Base exception for all PR Agent errors."""

    pass


class ConfigurationError(PRAgentError):
    """Raised when configuration is invalid or missing."""

    pass


class GitHubAPIError(PRAgentError):
    """Raised when GitHub API operations fail."""

    pass


class AnalysisError(PRAgentError):
    """Raised when analysis operations fail (non-fatal)."""

    pass


class AIError(PRAgentError):
    """Raised when AI operations fail (non-fatal, allows graceful degradation)."""

    pass


class FatalError(PRAgentError):
    """Raised for fatal errors that prevent the agent from continuing."""

    pass
