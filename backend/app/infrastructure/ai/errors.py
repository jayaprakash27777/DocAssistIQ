"""DocAssistIQ — AI Provider Error Definitions (Phase 16)."""

class AIProviderError(Exception):
    """Base class for all AI provider exceptions."""
    def __init__(self, message: str, provider_name: str, status_code: int | None = None):
        super().__init__(message)
        self.provider_name = provider_name
        self.status_code = status_code


class AIConnectionError(AIProviderError):
    """Raised when the provider is unreachable (timeout, DNS, etc)."""
    pass


class AIAuthenticationError(AIProviderError):
    """Raised when the provider rejects credentials."""
    pass


class AIRateLimitError(AIProviderError):
    """Raised when the provider rate limits requests (429)."""
    def __init__(self, message: str, provider_name: str, retry_after: int | None = None):
        super().__init__(message, provider_name, status_code=429)
        self.retry_after = retry_after


class AIContextLengthExceededError(AIProviderError):
    """Raised when the input exceeds the provider's token limit."""
    pass


class AIContentFilterError(AIProviderError):
    """Raised when the provider rejects the prompt due to safety/content filters."""
    pass
