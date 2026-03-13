from __future__ import annotations

from types import SimpleNamespace

import pytest

from freeloader.service_providers.domain import Credentials, MissingCredentialsError, ProviderDefinitionError
from freeloader.service_providers.infrastructure import catalog


def test_credentials_require_includes_provider_context() -> None:
    credentials = Credentials({"GITHUB_TOKEN": "token"})

    with pytest.raises(
        MissingCredentialsError,
        match="Provider 'github': Missing required credentials: COOLIFY_ENDPOINT.",
    ):
        credentials.require(["COOLIFY_ENDPOINT"], provider_name="github")


def test_catalog_loads_expected_provider_drivers() -> None:
    drivers = catalog._instantiate_drivers()

    assert {str(driver.provider.name) for driver in drivers} == {
        "aws",
        "coolify",
        "docker",
        "git",
        "github",
        "gitlab",
        "terraform",
    }


def test_catalog_requires_provider_driver_class(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_module = SimpleNamespace(__name__="fake.module")

    monkeypatch.setattr(catalog, "_discover_provider_modules",
                        lambda: ["fake.module"])
    monkeypatch.setattr(catalog.importlib, "import_module",
                        lambda _: fake_module)

    with pytest.raises(ProviderDefinitionError, match="ProviderDriver implementation"):
        catalog._instantiate_drivers()
