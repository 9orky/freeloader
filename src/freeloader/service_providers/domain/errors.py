class ServiceProvidersError(Exception):
    """Base error for the service providers feature."""


class UnknownProviderError(ServiceProvidersError):
    def __init__(self, provider_name: str) -> None:
        super().__init__(f"Unknown provider '{provider_name}'.")


class ProviderDefinitionError(ServiceProvidersError):
    def __init__(self, message: str, provider_name: str | None = None) -> None:
        if provider_name:
            message = f"Provider '{provider_name}': {message}"
        super().__init__(message)


class ProviderAuthError(ServiceProvidersError):
    def __init__(self, provider_name: str, message: str) -> None:
        super().__init__(
            f"Provider '{provider_name}' authentication failed: {message}")


class ProviderCapabilityError(ServiceProvidersError):
    def __init__(self, provider_name: str, capability: str) -> None:
        super().__init__(
            f"Provider '{provider_name}' does not support capability '{capability}'.")


class ProviderInstallationError(ServiceProvidersError):
    def __init__(self, provider_name: str, requirement: str) -> None:
        super().__init__(
            f"Provider '{provider_name}' requires local dependency '{requirement}'.")


class MissingCredentialsError(ServiceProvidersError):
    def __init__(self, missing_keys: list[str], provider_name: str | None = None) -> None:
        keys = ", ".join(missing_keys)
        message = f"Missing required credentials: {keys}."
        if provider_name:
            message = f"Provider '{provider_name}': {message}"
        super().__init__(message)
