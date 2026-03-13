from dataclasses import dataclass

from freeloader.service_providers import ServiceProviders
from freeloader.service_providers.application import queries
from freeloader.service_providers.domain import (
    DriverSupportReport,
    LocalCommand,
    LocalRequirement,
    ProviderName,
    ServiceProvider,
    UnknownProviderError,
)


@dataclass(frozen=True)
class FakeDriver:
    provider: ServiceProvider
    support_report: DriverSupportReport

    def check_local_support(self) -> DriverSupportReport:
        return self.support_report

    def validate_credentials(self, credentials) -> None:
        raise AssertionError("validate_credentials should not be called")

    def fetch_billing(self, credentials):
        raise AssertionError("fetch_billing should not be called")


@dataclass(frozen=True)
class FakeCatalog:
    drivers: dict[str, FakeDriver]

    def list_providers(self) -> list[ServiceProvider]:
        return [self.drivers[name].provider for name in sorted(self.drivers)]

    def get_provider(self, name: ProviderName | str) -> ServiceProvider:
        return self.get_driver(name).provider

    def get_driver(self, name: ProviderName | str) -> FakeDriver:
        normalized_name = str(ProviderName(str(name)))
        try:
            return self.drivers[normalized_name]
        except KeyError as exc:
            raise UnknownProviderError(normalized_name) from exc


def test_list_providers_returns_catalog_definitions(monkeypatch) -> None:
    monkeypatch.setattr(queries, "load_provider_catalog", lambda: _catalog())

    providers = queries.list_providers()

    assert [str(provider.name)
            for provider in providers] == ["docker", "git", "github"]


def test_check_block_support_aggregates_missing_local_commands(monkeypatch) -> None:
    monkeypatch.setattr(queries, "load_provider_catalog", lambda: _catalog())

    report = ServiceProviders().check_block_support(
        [" docker ", "git", "docker"])

    assert report.supported is False
    assert report.missing_local_commands == (LocalCommand("docker"),)
    assert report.reasons == ("Docker CLI not found in PATH.",)
    assert [str(driver_report.driver) for driver_report in report.driver_reports] == [
        "docker",
        "git",
    ]


def test_is_block_supported_returns_boolean(monkeypatch) -> None:
    monkeypatch.setattr(queries, "load_provider_catalog", lambda: _catalog())

    supported = ServiceProviders().is_block_supported(["git"])

    assert supported is True


def test_package_root_exports_service_providers_facade() -> None:
    from freeloader import service_providers

    assert service_providers.ServiceProviders is ServiceProviders


def _catalog() -> FakeCatalog:
    git_provider = ServiceProvider(
        name="git",
        support=(LocalRequirement("git"),),
    )
    docker_provider = ServiceProvider(
        name="docker",
        support=(LocalRequirement("docker"),),
    )
    github_provider = ServiceProvider(
        name="github",
        support=(LocalRequirement("gh"),),
    )
    return FakeCatalog(
        drivers={
            "docker": FakeDriver(
                provider=docker_provider,
                support_report=DriverSupportReport(
                    driver="docker",
                    missing_local_commands=(LocalCommand("docker"),),
                    reasons=("Docker CLI not found in PATH.",),
                ),
            ),
            "git": FakeDriver(
                provider=git_provider,
                support_report=DriverSupportReport(driver="git"),
            ),
            "github": FakeDriver(
                provider=github_provider,
                support_report=DriverSupportReport(driver="github"),
            ),
        }
    )
