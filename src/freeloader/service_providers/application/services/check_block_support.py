from freeloader.service_providers.domain import BlockSupportReport, ProviderName
from freeloader.service_providers.domain.repository import ProviderCatalog


class CheckBlockSupportService:
    def __init__(self, provider_catalog: ProviderCatalog) -> None:
        self._provider_catalog = provider_catalog

    def check(self, driver_names: list[str]) -> BlockSupportReport:
        normalized_names = tuple(dict.fromkeys(
            ProviderName(name) for name in driver_names))
        driver_reports = tuple(
            self._provider_catalog.get_driver(name).check_local_support()
            for name in normalized_names
        )
        return BlockSupportReport(driver_reports=driver_reports)

    def is_supported(self, driver_names: list[str]) -> bool:
        return self.check(driver_names).supported
