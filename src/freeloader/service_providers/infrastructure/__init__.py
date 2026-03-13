from __future__ import annotations

from functools import cache

from ..domain.repository import CredentialRepository, ProviderCatalog
from .catalog import ProviderCatalogImpl, _instantiate_drivers
from .secrets import SecretsCredentialRepository


@cache
def load_provider_catalog() -> ProviderCatalog:
    return ProviderCatalogImpl(_instantiate_drivers())


def load_credential_repository() -> CredentialRepository:
    return SecretsCredentialRepository()


__all__ = [
    "load_credential_repository",
    "load_provider_catalog",
]
