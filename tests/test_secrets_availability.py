from dataclasses import dataclass

from freeloader.secrets.application import commands
from freeloader.secrets.application.interface import Secrets


@dataclass(frozen=True)
class FakeSecretRepository:
    available: set[tuple[str | None, str]]

    def has(self, key: str, namespace: str | None = None) -> bool:
        return (namespace, key) in self.available

    def get(self, key: str, namespace: str | None = None):
        raise AssertionError("secret values must not be read for availability checks")


def test_check_secret_availability_reports_present_and_missing_keys(monkeypatch) -> None:
    monkeypatch.setattr(
        commands,
        "load_secret_repository",
        lambda: FakeSecretRepository(
            available={
                ("global", "github_token"),
                ("global", "gitlab_token"),
            }
        ),
    )

    report = commands.check_secret_availability(
        ["github_token", "missing_token", "github_token"],
        namespace="global",
    )

    assert report.required_keys == ("github_token", "missing_token")
    assert report.present_keys == ("github_token",)
    assert report.missing_keys == ("missing_token",)
    assert report.available is False


def test_secrets_facade_normalizes_names_for_availability(monkeypatch) -> None:
    monkeypatch.setattr(
        commands,
        "load_secret_repository",
        lambda: FakeSecretRepository(available={("workspace", "github_token")}),
    )

    report = Secrets(namespace="workspace").check_availability(
        [" GITHUB_TOKEN "]
    )

    assert report.required_keys == ("github_token",)
    assert report.present_keys == ("github_token",)
    assert report.missing_keys == ()
    assert report.available is True
