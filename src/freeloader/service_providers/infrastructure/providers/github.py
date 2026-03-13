from __future__ import annotations

from datetime import datetime, timezone

from freeloader.service_providers.domain import (
    AuthSpec,
    BillingCheckCost,
    BillingLineItem,
    BillingReport,
    BillingSpec,
    CredentialKey,
    Credentials,
    DriverSupportReport,
    FreeTierUsage,
    ObtainCredentialAction,
    ObtainCredentialStep,
    ProviderAuthError,
    ServiceProvider,
)
from freeloader.service_providers.domain.repository import ProviderDriver


class GitHubDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="github",
            auth=AuthSpec(
                credential_keys=(CredentialKey("GITHUB_TOKEN"),),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.info,
                        value="Create a Personal Access Token with repo scope.",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="https://github.com/settings/tokens/new",
                    ),
                ),
            ),
            billing=BillingSpec(BillingCheckCost.free),
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

        from github import Auth, BadCredentialsException, Github

        client = Github(auth=Auth.Token(credentials["GITHUB_TOKEN"]))
        try:
            client.get_user()
        except BadCredentialsException as exc:
            raise ProviderAuthError("github", "Invalid GitHub token.") from exc

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        auth = self.provider.auth
        assert auth is not None
        credentials = credentials.require(
            auth.credential_keys,
            provider_name=str(self.provider.name),
        )

        from github import Auth, Github

        client = Github(auth=Auth.Token(credentials["GITHUB_TOKEN"]))
        actions_billing = client.requester.requestJsonAndCheck(
            "GET", "/user/settings/billing/actions"
        )[1]
        storage_billing = client.requester.requestJsonAndCheck(
            "GET", "/user/settings/billing/shared-storage"
        )[1]

        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")

        minutes_used = float(actions_billing.get("total_minutes_used", 0))
        minutes_included = float(actions_billing.get("included_minutes", 0))
        minutes_paid = float(actions_billing.get("total_paid_minutes_used", 0))

        storage_used_gb = float(storage_billing.get(
            "estimated_storage_for_month", 0))
        storage_paid_gb = float(storage_billing.get(
            "estimated_paid_storage_for_month", 0))

        items: list[BillingLineItem] = []
        if minutes_paid > 0:
            items.append(
                BillingLineItem(
                    service="Actions Minutes (overage)",
                    amount_usd=minutes_paid,
                )
            )
        if storage_paid_gb > 0:
            items.append(
                BillingLineItem(
                    service="Shared Storage (overage)",
                    amount_usd=storage_paid_gb,
                )
            )

        return BillingReport(
            provider=self.provider.name,
            total_usd=round(sum(item.amount_usd for item in items), 4),
            period=period,
            items=tuple(items),
            free_tier_usage=(
                FreeTierUsage(
                    service="GitHub Actions",
                    metric="minutes",
                    used=minutes_used,
                    limit=minutes_included,
                    unit="minutes/month",
                ),
                FreeTierUsage(
                    service="Shared Storage",
                    metric="storage",
                    used=storage_used_gb,
                    limit=0.5,
                    unit="GB",
                ),
            ),
        )
