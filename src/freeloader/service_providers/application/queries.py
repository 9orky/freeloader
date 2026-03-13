from ..domain import BillingReport, BlockSupportReport, ServiceProvider
from ..infrastructure import (
    load_credential_repository,
    load_provider_catalog,
)

from .services.check_block_support import CheckBlockSupportService
from .services.fetch_billing import FetchBillingService


def list_providers() -> list[ServiceProvider]:
    return load_provider_catalog().list_providers()


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
    "list_providers",
]
