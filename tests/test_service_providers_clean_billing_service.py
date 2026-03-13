from dataclasses import dataclass, field

import pytest

from freeloader.service_providers.application.services.fetch_billing import FetchBillingService
from freeloader.service_providers.domain import (
    AuthSpec,
    BillingCheckCost,
    BillingReport,
    BillingSpec,
    CredentialKey,
    Credentials,
    LocalRequirement,
    MissingCredentialsError,
    ProviderCapabilityError,
    ProviderName,
    ServiceProvider,
    UnknownProviderError,
)


@dataclass
class FakeDriver:
    provider: ServiceProvider
    report: BillingReport | None = None
    received_credentials: dict[str, str] | None = None

    def check_local_support(self):
        raise AssertionError("check_local_support should not be called")

    def validate_credentials(self, credentials: Credentials) -> None:
        raise AssertionError("validate_credentials should not be called")

    def fetch_billing(self, credentials: Credentials) -> BillingReport:
        self.received_credentials = credentials.to_dict()
        assert self.report is not None
        return self.report


@dataclass
class FakeCatalog:
    drivers: dict[str, FakeDriver]

    def list_providers(self) -> list[ServiceProvider]:
        return [driver.provider for driver in self.drivers.values()]

    def get_provider(self, name: ProviderName | str) -> ServiceProvider:
        return self.get_driver(name).provider

    def get_driver(self, name: ProviderName | str) -> FakeDriver:
        normalized_name = str(ProviderName(str(name)))
        try:
            return self.drivers[normalized_name]
        except KeyError as exc:
            raise UnknownProviderError(normalized_name) from exc


@dataclass
class FakeCredentialRepository:
    stored: dict[str, str] = field(default_factory=dict)

    def read_credentials(self, keys: list[CredentialKey]) -> Credentials:
        values = {
            str(key): self.stored[str(key)]
            for key in keys
            if str(key) in self.stored
        }
        return Credentials(values)

    def write_credentials(self, credentials: Credentials) -> None:
        raise AssertionError("write_credentials should not be called")


def test_fetch_billing_returns_report_with_stored_credentials() -> None:
    driver = FakeDriver(
        provider=_billing_provider(),
        report=BillingReport(
            provider="github", total_usd=0.0, period="2026-03"),
    )
    service = FetchBillingService(
        provider_catalog=FakeCatalog(drivers={"github": driver}),
        credential_repository=FakeCredentialRepository(
            stored={"GITHUB_TOKEN": "token"}
        ),
    )

    report = service.fetch("github")

    assert str(report.provider) == "github"
    assert driver.received_credentials == {"GITHUB_TOKEN": "token"}


def test_fetch_billing_fails_cleanly_for_unsupported_provider() -> None:
    driver = FakeDriver(provider=_local_provider())
    service = FetchBillingService(
        provider_catalog=FakeCatalog(drivers={"docker": driver}),
        credential_repository=FakeCredentialRepository(),
    )

    with pytest.raises(
        ProviderCapabilityError,
        match="Provider 'docker' does not support capability 'billing'.",
    ):
        service.fetch("docker")


def test_fetch_billing_raises_domain_error_for_missing_stored_credentials() -> None:
    service = FetchBillingService(
        provider_catalog=FakeCatalog(
            drivers={"github": FakeDriver(provider=_billing_provider())}),
        credential_repository=FakeCredentialRepository(),
    )

    with pytest.raises(
        MissingCredentialsError,
        match="Provider 'github': Missing required credentials: GITHUB_TOKEN.",
    ):
        service.fetch("github")


def _billing_provider() -> ServiceProvider:
    return ServiceProvider(
        name="github",
        auth=AuthSpec((CredentialKey("GITHUB_TOKEN"),)),
        billing=BillingSpec(BillingCheckCost.free),
    )


def _local_provider() -> ServiceProvider:
    return ServiceProvider(
        name="docker",
        support=(LocalRequirement("docker"),),
    )
