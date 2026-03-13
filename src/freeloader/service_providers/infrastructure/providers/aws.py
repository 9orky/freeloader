from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

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


class AWSDriver(ProviderDriver):
    def __init__(self) -> None:
        self.provider = ServiceProvider(
            name="aws",
            auth=AuthSpec(
                credential_keys=(
                    CredentialKey("AWS_ACCESS_KEY_ID"),
                    CredentialKey("AWS_SECRET_ACCESS_KEY"),
                ),
                obtain_steps=(
                    ObtainCredentialStep(
                        action=ObtainCredentialAction.open_url,
                        value="https://console.aws.amazon.com/iam/home#/security_credentials",
                    ),
                ),
            ),
            billing=BillingSpec(BillingCheckCost.paid),
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

        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError

        session = boto3.Session(
            aws_access_key_id=credentials["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=credentials["AWS_SECRET_ACCESS_KEY"],
            region_name=self._region(credentials, default="eu-central-1"),
        )
        try:
            session.client("sts").get_caller_identity()
        except (ClientError, NoCredentialsError) as exc:
            raise ProviderAuthError("aws", "Invalid AWS credentials.") from exc

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        auth = self.provider.auth
        assert auth is not None
        credentials = credentials.require(
            auth.credential_keys,
            provider_name=str(self.provider.name),
        )

        import boto3
        from botocore.exceptions import ClientError

        session = boto3.Session(
            aws_access_key_id=credentials["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=credentials["AWS_SECRET_ACCESS_KEY"],
            region_name=self._region(credentials, default="us-east-1"),
        )

        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-01")
        end = now.strftime("%Y-%m-%d")

        response = session.client("ce", region_name="us-east-1").get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        items: list[BillingLineItem] = []
        total = 0.0
        groups = response.get("ResultsByTime", [{}])[0].get("Groups", [])
        for group in groups:
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            currency = group["Metrics"]["UnblendedCost"]["Unit"]
            total += amount
            items.append(
                BillingLineItem(
                    service=group["Keys"][0],
                    amount_usd=amount,
                    currency=currency,
                )
            )

        free_tier_usage = self._fetch_free_tier(session, ClientError)
        return BillingReport(
            provider=self.provider.name,
            total_usd=round(total, 4),
            period=f"{start} to {end}",
            items=tuple(items),
            free_tier_usage=tuple(free_tier_usage),
        )

    def _fetch_free_tier(self, session: Any, client_error_type: type[Exception]) -> list[FreeTierUsage]:
        try:
            response = session.client(
                "freetier", region_name="us-east-1").get_free_tier_usage()
        except client_error_type:
            return []

        return [
            FreeTierUsage(
                service=entry.get("service", ""),
                metric=entry.get("usageType", ""),
                used=float(entry.get("actualUsageAmount", 0)),
                limit=float(entry.get("forecastedUsageAmount", 0)),
                unit=entry.get("unit", ""),
            )
            for entry in response.get("freeTierUsages", [])
        ]

    def _region(self, credentials: Credentials, *, default: str) -> str:
        if "AWS_REGION" in credentials:
            return credentials["AWS_REGION"]
        return default
