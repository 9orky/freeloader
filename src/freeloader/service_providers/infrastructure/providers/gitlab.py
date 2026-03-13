from __future__ import annotations

from datetime import datetime, timezone

from freeloader.service_providers.domain import (
    AuthSpec,
    BillingCheckCost,
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


class GitLabDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="gitlab",
            auth=AuthSpec(
                credential_keys=(CredentialKey("GITLAB_TOKEN"),),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.info,
                        value="Create a Personal Access Token with api scope.",
                    ),
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="https://gitlab.com/-/user_settings/personal_access_tokens",
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

        from gitlab import Gitlab, GitlabAuthenticationError

        try:
            Gitlab(private_token=credentials["GITLAB_TOKEN"]).auth()
        except GitlabAuthenticationError as exc:
            raise ProviderAuthError("gitlab", "Invalid GitLab token.") from exc

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        auth = self.provider.auth
        assert auth is not None
        credentials = credentials.require(
            auth.credential_keys,
            provider_name=str(self.provider.name),
        )

        from gitlab import Gitlab

        client = Gitlab(private_token=credentials["GITLAB_TOKEN"])
        client.auth()

        user = client.user
        if user is None or not getattr(user, "username", None):
            raise ProviderAuthError(
                "gitlab", "Unable to resolve GitLab user profile.")
        namespace = client.namespaces.get(user.username)
        now = datetime.now(timezone.utc)

        storage_size = float(getattr(namespace, "storage_size_limit", 0) or 0)
        storage_used = float(getattr(namespace, "storage_size", 0) or 0)

        storage_limit_gb = storage_size / \
            (1024 ** 3) if storage_size > 0 else 5.0
        storage_used_gb = storage_used / (1024 ** 3)

        ci_minutes_used = 0.0
        ci_minutes_limit = 400.0
        if hasattr(namespace, "extra_shared_runners_minutes_limit"):
            ci_minutes_limit = float(
                getattr(namespace, "shared_runners_minutes_limit", 400))
            ci_minutes_used = ci_minutes_limit - float(
                getattr(namespace, "extra_shared_runners_minutes_limit", 0)
            )

        return BillingReport(
            provider=self.provider.name,
            total_usd=0.0,
            period=now.strftime("%Y-%m"),
            free_tier_usage=(
                FreeTierUsage(
                    service="GitLab CI/CD",
                    metric="compute_minutes",
                    used=ci_minutes_used,
                    limit=ci_minutes_limit,
                    unit="minutes/month",
                ),
                FreeTierUsage(
                    service="GitLab Storage",
                    metric="storage",
                    used=round(storage_used_gb, 4),
                    limit=round(storage_limit_gb, 4),
                    unit="GB",
                ),
            ),
        )
