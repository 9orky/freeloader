from dataclasses import dataclass, field

import pytest

from freeloader.service_providers.application.services.authorize_provider import (
    AuthorizeProviderService,
)
from freeloader.service_providers.domain import (
    AuthSpec,
    CredentialKey,
    Credentials,
    DriverSupportReport,
    LocalRequirement,
    MissingCredentialsError,
    ProviderAuthError,
    ProviderName,
    ServiceProvider,
    UnknownProviderError,
)


@dataclass
class FakeDriver:
    provider: ServiceProvider
    support_report: DriverSupportReport = field(
        default_factory=lambda: DriverSupportReport(driver="fake"))

    def check_local_support(self) -> DriverSupportReport:
        return self.support_report

    def validate_credentials(self, credentials: Credentials) -> None:
        if self.provider.requires_auth and credentials["GITHUB_TOKEN"] == "bad-token":
            raise ProviderAuthError(
                str(self.provider.name), "Invalid GitHub token.")

    def fetch_billing(self, credentials: Credentials):
        raise AssertionError("fetch_billing should not be called")


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
    writes: list[dict[str, str]] = field(default_factory=list)

    def read_credentials(self, keys: list[CredentialKey]) -> Credentials:
        raise AssertionError("read_credentials should not be called")

    def write_credentials(self, credentials: Credentials) -> None:
        self.writes.append(credentials.to_dict())


def test_authorize_succeeds_for_auth_free_provider_without_storing_credentials() -> None:
    repository = FakeCredentialRepository()
    service = AuthorizeProviderService(
        provider_catalog=FakeCatalog(
            drivers={"git": FakeDriver(_local_provider())}),
        credential_repository=repository,
    )

    result = service.authorize("git", {"IGNORED": "value"})

    assert str(result.provider) == "git"
    assert result.stored_credentials == ()
    assert repository.writes == []


def test_authorize_persists_declared_credentials_for_auth_required_provider() -> None:
    repository = FakeCredentialRepository()
    service = AuthorizeProviderService(
        provider_catalog=FakeCatalog(
            drivers={"github": FakeDriver(_auth_provider())}),
        credential_repository=repository,
    )

    result = service.authorize(
        "github",
        {"github_token": "token", "EXTRA_VALUE": "ignored"},
    )

    assert str(result.provider) == "github"
    assert tuple(str(key)
                 for key in result.stored_credentials) == ("GITHUB_TOKEN",)
    assert repository.writes == [{"GITHUB_TOKEN": "token"}]


def test_authorize_fails_cleanly_on_missing_credentials() -> None:
    service = AuthorizeProviderService(
        provider_catalog=FakeCatalog(
            drivers={"github": FakeDriver(_auth_provider())}),
        credential_repository=FakeCredentialRepository(),
    )

    with pytest.raises(
        MissingCredentialsError,
        match="Provider 'github': Missing required credentials: GITHUB_TOKEN.",
    ):
        service.authorize("github", {})


def test_authorize_fails_cleanly_on_invalid_credentials() -> None:
    service = AuthorizeProviderService(
        provider_catalog=FakeCatalog(
            drivers={"github": FakeDriver(_auth_provider())}),
        credential_repository=FakeCredentialRepository(),
    )

    with pytest.raises(
        ProviderAuthError,
        match="Provider 'github' authentication failed: Invalid GitHub token.",
    ):
        service.authorize("github", {"GITHUB_TOKEN": "bad-token"})


def _local_provider() -> ServiceProvider:
    return ServiceProvider(
        name="git",
        support=(LocalRequirement("git"),),
    )


def _auth_provider() -> ServiceProvider:
    return ServiceProvider(
        name="github",
        auth=AuthSpec((CredentialKey("GITHUB_TOKEN"),)),
    )
