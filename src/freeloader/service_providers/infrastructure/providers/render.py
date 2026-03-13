from __future__ import annotations

import httpx

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


class RenderDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="render",
            auth=AuthSpec(
                credential_keys=(CredentialKey("RENDER_API_KEY"),),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.info,
                        value="Create a Render API key from your account settings.",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="https://dashboard.render.com/u/settings?add-api-key",
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

        try:
            response = httpx.get(
                "https://api.render.com/v1/users",
                headers={
                    "Accept": "application/json",
                    "Authorization": f"Bearer {credentials['RENDER_API_KEY']}",
                },
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            raise ProviderAuthError(
                "render", "Unable to reach the Render API."
            ) from exc

        if response.status_code == 401:
            raise ProviderAuthError("render", "Invalid Render API key.")
        if response.status_code >= 400:
            raise ProviderAuthError(
                "render",
                f"Render API validation failed with status {response.status_code}.",
            )

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        raise ProviderCapabilityError(str(self.provider.name), "billing")
