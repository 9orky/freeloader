import importlib

from freeloader.service_providers import usecases


def test_service_providers_package_and_usecases_are_importable() -> None:
    importlib.import_module("freeloader.service_providers")
    importlib.import_module("freeloader.service_providers.usecases")


def test_list_providers_returns_registered_provider_names() -> None:
    provider_names = {provider.name for provider in usecases.list_providers()}

    assert {"aws", "coolify", "docker", "git", "github", "gitlab"}.issubset(provider_names)


def test_get_provider_returns_auth_metadata() -> None:
    provider = usecases.get_provider("github")

    assert provider.name == "github"
    assert provider.requires_auth is True
    assert provider.auth_keys == ["GITHUB_TOKEN"]
    assert provider.obtain_token_steps