from dataclasses import dataclass

from ..domain import BillingReport, BlockSupportReport, ServiceProvider
from ..infrastructure import (
    load_credential_repository,
    load_provider_catalog,
)

from .services.check_block_support import CheckBlockSupportService
from .services.fetch_billing import FetchBillingService


@dataclass(frozen=True)
class ProviderListItem:
    provider: ServiceProvider
    authorized: bool | None


def list_providers() -> list[ServiceProvider]:
    return load_provider_catalog().list_providers()


def list_provider_items() -> list[ProviderListItem]:
    catalog = load_provider_catalog()
    credential_repository = load_credential_repository()

    items: list[ProviderListItem] = []
    for provider in catalog.list_providers():
        authorized: bool | None = None
        if provider.requires_auth:
            auth = provider.auth
            if auth is not None:
                credentials = credential_repository.read_credentials(
                    list(auth.credential_keys)
                )
                authorized = all(
                    key in credentials for key in auth.credential_keys)

        items.append(ProviderListItem(
            provider=provider, authorized=authorized))

    return items


def get_provider(name: str) -> ServiceProvider:
    return load_provider_catalog().get_provider(name)


def check_billing(name: str) -> BillingReport:
    service = FetchBillingService(
        provider_catalog=load_provider_catalog(),
        credential_repository=load_credential_repository(),
    )
    return service.fetch(name)


def check_block_support(driver_names: list[str]) -> BlockSupportReport:
    service = CheckBlockSupportService(
        provider_catalog=load_provider_catalog())
    return service.check(driver_names)


__all__ = [
    "check_billing",
    "check_block_support",
    "get_provider",
    "ProviderListItem",
    "list_provider_items",
    "list_providers",
]
