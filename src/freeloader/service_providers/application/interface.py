from dataclasses import dataclass

from ..domain import (
    AuthorizationResult,
    BillingReport,
    BlockSupportReport,
    ProviderName,
)

from . import commands, queries


@dataclass(frozen=True)
class ServiceProviders:
    def authorize_provider(
        self,
        name: str,
        credentials: dict[str, str],
    ) -> AuthorizationResult:
        return commands.authorize_provider(
            self._normalize_provider_name(name),
            credentials,
        )

    def check_billing(self, name: str) -> BillingReport:
        return queries.check_billing(self._normalize_provider_name(name))

    def check_block_support(self, driver_names: list[str]) -> BlockSupportReport:
        return queries.check_block_support(
            [self._normalize_provider_name(name) for name in driver_names]
        )

    def is_block_supported(self, driver_names: list[str]) -> bool:
        return self.check_block_support(driver_names).supported

    @staticmethod
    def _normalize_provider_name(name: str) -> str:
        return str(ProviderName(name))
