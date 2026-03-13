from collections.abc import Mapping

from freeloader.service_providers.domain import (
    AuthorizationResult,
    CredentialKey,
    CredentialValue,
    Credentials,
    DriverSupportReport,
    ProviderInstallationError,
)
from freeloader.service_providers.domain.repository import CredentialRepository, ProviderCatalog


class AuthorizeProviderService:
    def __init__(
        self,
        provider_catalog: ProviderCatalog,
        credential_repository: CredentialRepository,
    ) -> None:
        self._provider_catalog = provider_catalog
        self._credential_repository = credential_repository

    def authorize(self, name: str, credentials: Mapping[str, str]) -> AuthorizationResult:
        provider = self._provider_catalog.get_provider(name)
        driver = self._provider_catalog.get_driver(provider.name)
        support_report = driver.check_local_support()
        if not support_report.supported:
            raise ProviderInstallationError(
                str(provider.name),
                self._installation_requirement(support_report),
            )

        if not provider.requires_auth:
            return AuthorizationResult(provider=provider.name, stored_credentials=())

        auth = provider.auth
        assert auth is not None

        provided_credentials = Credentials(
            {
                CredentialKey(key): CredentialValue(value)
                for key, value in credentials.items()
            }
        )
        stored_credentials = provided_credentials.require(
            auth.credential_keys,
            provider_name=str(provider.name),
        )
        driver.validate_credentials(provided_credentials)
        self._credential_repository.write_credentials(stored_credentials)

        return AuthorizationResult(
            provider=provider.name,
            stored_credentials=auth.credential_keys,
        )

    @staticmethod
    def _installation_requirement(support_report: DriverSupportReport) -> str:
        if support_report.missing_local_commands:
            return str(support_report.missing_local_commands[0])
        if support_report.reasons:
            return support_report.reasons[0]
        return "unknown"
