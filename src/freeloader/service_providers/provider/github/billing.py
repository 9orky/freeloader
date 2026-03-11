from datetime import datetime, timezone

from github import Github, Auth

from ..auth import Credentials
from ..billing import (
    BillingAdapter,
    BillingCheckCost,
    BillingLineItem,
    BillingReport,
    FreeTierUsage,
    billing_adapters,
)


@billing_adapters.register("github")
class GitHubBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.free

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        auth = Auth.Token(credentials.kv["GITHUB_TOKEN"])
        gh = Github(auth=auth)

        actions = gh.get_user().get_repos()
        actions_billing = gh.requester.requestJsonAndCheck(
            "GET", "/user/settings/billing/actions")[1]
        storage_billing = gh.requester.requestJsonAndCheck(
            "GET", "/user/settings/billing/shared-storage")[1]

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
            items.append(BillingLineItem(
                service="Actions Minutes (overage)", amount_usd=minutes_paid))
        if storage_paid_gb > 0:
            items.append(BillingLineItem(
                service="Shared Storage (overage)", amount_usd=storage_paid_gb))

        total = sum(item.amount_usd for item in items)

        free_tier_usage: list[FreeTierUsage] = [
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
        ]

        return BillingReport(
            provider="github",
            total_usd=round(total, 4),
            period=period,
            items=items,
            free_tier_usage=free_tier_usage,
        )
