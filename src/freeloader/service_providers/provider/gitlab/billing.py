from datetime import datetime, timezone

from gitlab import Gitlab

from ..auth import Credentials
from ..billing import (
    BillingAdapter,
    BillingCheckCost,
    BillingLineItem,
    BillingReport,
    FreeTierUsage,
    billing_adapters,
)


@billing_adapters.register("gitlab")
class GitLabBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.free

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        gl = Gitlab(private_token=credentials.kv["GITLAB_TOKEN"])
        gl.auth()

        user = gl.user
        namespace = gl.namespaces.get(user.username)

        now = datetime.now(timezone.utc)
        period = now.strftime("%Y-%m")

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

        items: list[BillingLineItem] = []
        total = 0.0

        free_tier_usage: list[FreeTierUsage] = [
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
        ]

        return BillingReport(
            provider="gitlab",
            total_usd=total,
            period=period,
            items=items,
            free_tier_usage=free_tier_usage,
        )
