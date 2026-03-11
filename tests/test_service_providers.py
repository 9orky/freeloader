import importlib

from freeloader.service_providers.ports import interface


def test_service_providers_package_and_interface_are_importable() -> None:
    importlib.import_module("freeloader.service_providers")
    importlib.import_module("freeloader.service_providers.ports.interface")


def test_list_providers_returns_registered_provider_names() -> None:
    provider_names = {provider.name for provider in interface.list_providers()}

    assert {"aws", "coolify", "docker", "git",
            "github", "gitlab"}.issubset(provider_names)


def test_get_provider_returns_auth_metadata() -> None:
    provider = interface.get_provider("github")

    assert provider.name == "github"
    assert provider.requires_auth is True
    assert provider.auth_keys == ["GITHUB_TOKEN"]
    assert provider.obtain_token_steps
    assert provider.supports_billing is True


def test_write_credentials_batches_secret_writes(monkeypatch) -> None:
    from freeloader.service_providers.adapters import secrets as secrets_adapter

    calls: list[dict[str, str]] = []

    class FakeSecrets:
        def write_secrets(self, values: dict[str, str]) -> None:
            calls.append(values)

    monkeypatch.setattr(
        secrets_adapter.Secrets,
        "for_default_namespace",
        classmethod(lambda cls: FakeSecrets()),
    )

    secrets_adapter.write_credentials(
        {"GITHUB_TOKEN": "token", "AWS_SECRET": "secret"})

    assert calls == [{"GITHUB_TOKEN": "token", "AWS_SECRET": "secret"}]
