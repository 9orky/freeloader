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


class VercelDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="vercel",
            auth=AuthSpec(
                credential_keys=(CredentialKey("VERCEL_TOKEN"),),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.info,
                        value="Create a Vercel access token from your account settings.",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="https://vercel.com/account/tokens",
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
                "https://api.vercel.com/v3/events",
                params={"limit": 1},
                headers={
                    "Authorization": f"Bearer {credentials['VERCEL_TOKEN']}"},
                timeout=10.0,
            )
        except httpx.HTTPError as exc:
            raise ProviderAuthError(
                "vercel", "Unable to reach the Vercel API."
            ) from exc

        if response.status_code in {401, 403}:
            raise ProviderAuthError("vercel", "Invalid Vercel token.")
        if response.status_code >= 400:
            raise ProviderAuthError(
                "vercel",
                f"Vercel API validation failed with status {response.status_code}.",
            )

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        raise ProviderCapabilityError(str(self.provider.name), "billing")
