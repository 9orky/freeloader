from ..domain import AuthorizationResult
from ..infrastructure import (
    load_credential_repository,
    load_provider_catalog,
)

from .services.authorize_provider import AuthorizeProviderService


def authorize_provider(name: str, credentials: dict[str, str]) -> AuthorizationResult:
    service = AuthorizeProviderService(
        provider_catalog=load_provider_catalog(),
        credential_repository=load_credential_repository(),
    )
    return service.authorize(name, credentials)


__all__ = ["authorize_provider"]
