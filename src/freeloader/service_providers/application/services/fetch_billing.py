from freeloader.service_providers.domain import BillingReport, Credentials, ProviderCapabilityError
from freeloader.service_providers.domain.repository import CredentialRepository, ProviderCatalog


class FetchBillingService:
    def __init__(
        self,
        provider_catalog: ProviderCatalog,
        credential_repository: CredentialRepository,
    ) -> None:
        self._provider_catalog = provider_catalog
        self._credential_repository = credential_repository

    def fetch(self, name: str) -> BillingReport:
        provider = self._provider_catalog.get_provider(name)
        if not provider.supports_billing:
            raise ProviderCapabilityError(str(provider.name), "billing")

        driver = self._provider_catalog.get_driver(provider.name)
        credentials = Credentials()
        if provider.requires_auth:
            auth = provider.auth
            assert auth is not None
            credentials = self._credential_repository.read_credentials(
                list(auth.credential_keys)
            ).require(
                auth.credential_keys,
                provider_name=str(provider.name),
            )

        return driver.fetch_billing(credentials)
