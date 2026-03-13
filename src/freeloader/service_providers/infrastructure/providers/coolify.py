from __future__ import annotations

from freeloader.service_providers.domain import (
    AuthSpec,
    BillingReport,
    CredentialKey,
    Credentials,
    DriverSupportReport,
    ObtainCredentialAction,
    ObtainCredentialStep,
    ProviderAuthError,
    ProviderCapabilityError,
    ServiceProvider,
)
from freeloader.service_providers.domain.repository import ProviderDriver


class CoolifyDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="coolify",
            auth=AuthSpec(
                credential_keys=(
                    CredentialKey("COOLIFY_TOKEN"),
                    CredentialKey("COOLIFY_ENDPOINT"),
                ),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.input,
                        value="COOLIFY_ENDPOINT",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.info,
                        value="Generate an API token from your Coolify dashboard.",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="{COOLIFY_ENDPOINT}/settings/api-tokens",
                    ),
                ),
            ),
        )

    def check_local_support(self) -> DriverSupportReport:
        return DriverSupportReport(driver=self.provider.name)

    def validate_credentials(self, credentials: Credentials) -> None:
        auth = self.provider.auth
        assert auth is not None
        credentials = credentials.require(
            auth.credential_keys,
            provider_name=str(self.provider.name),
        )

        from coolipy import Coolipy, exceptions

        client = Coolipy(
            coolify_api_key=credentials["COOLIFY_TOKEN"],
            coolify_endpoint=credentials["COOLIFY_ENDPOINT"],
        )
        try:
            client.healthcheck()
        except exceptions.CoolipyAPIServiceException as exc:
            raise ProviderAuthError(
                "coolify", "Invalid Coolify credentials.") from exc

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        raise ProviderCapabilityError(str(self.provider.name), "billing")
