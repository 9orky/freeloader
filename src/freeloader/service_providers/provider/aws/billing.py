from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

from ..auth import Credentials
from ..billing import (
    BillingAdapter,
    BillingCheckCost,
    BillingLineItem,
    BillingReport,
    FreeTierUsage,
    billing_adapters,
)


@billing_adapters.register("aws")
class AWSBilling(BillingAdapter):
    billing_check_cost = BillingCheckCost.paid

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        session = boto3.Session(
            aws_access_key_id=credentials.kv["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=credentials.kv["AWS_SECRET_ACCESS_KEY"],
            region_name=credentials.kv.get("AWS_REGION", "us-east-1"),
        )
        ce = session.client("ce", region_name="us-east-1")

        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-01")
        end = now.strftime("%Y-%m-%d")

        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        items: list[BillingLineItem] = []
        total = 0.0
        for group in response.get("ResultsByTime", [{}])[0].get("Groups", []):
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            currency = group["Metrics"]["UnblendedCost"]["Unit"]
            total += amount
            items.append(BillingLineItem(
                service=service,
                amount_usd=amount,
                currency=currency,
            ))

        free_tier_usage = self._fetch_free_tier(session)

        period = f"{start} to {end}"
        return BillingReport(
            provider="aws",
            total_usd=round(total, 4),
            period=period,
            items=items,
            free_tier_usage=free_tier_usage,
        )

    def _fetch_free_tier(self, session: boto3.Session) -> list[FreeTierUsage]:
        try:
            ft = session.client("freetier", region_name="us-east-1")
            response = ft.get_free_tier_usage()
        except ClientError:
            return []

        result: list[FreeTierUsage] = []
        for entry in response.get("freeTierUsages", []):
            result.append(FreeTierUsage(
                service=entry.get("service", ""),
                metric=entry.get("usageType", ""),
                used=float(entry.get("actualUsageAmount", 0)),
                limit=float(entry.get("forecastedUsageAmount", 0)),
                unit=entry.get("unit", ""),
            ))
        return result
