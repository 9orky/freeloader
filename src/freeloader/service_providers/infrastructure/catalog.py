from __future__ import annotations

import importlib
import inspect
import pkgutil
from types import ModuleType
from types import MappingProxyType

from ..domain import ProviderDefinitionError, ProviderName, ServiceProvider, UnknownProviderError
from ..domain.repository import ProviderCatalog, ProviderDriver
from . import providers as provider_package


def _discover_provider_modules() -> list[str]:
    module_names: list[str] = []
    for module_info in pkgutil.iter_modules(
        provider_package.__path__, f"{provider_package.__name__}."
    ):
        module_name = module_info.name.rsplit(".", 1)[-1]
        if module_name == "__init__" or module_name.startswith("_"):
            continue
        module_names.append(module_info.name)
    return sorted(module_names)


def _instantiate_drivers() -> list[ProviderDriver]:
    drivers: list[ProviderDriver] = []
    for module_name in _discover_provider_modules():
        module = importlib.import_module(module_name)
        driver = _discover_driver_class(module)()
        _validate_driver(driver)
        drivers.append(driver)

    return drivers


def _discover_driver_class(module: ModuleType) -> type[ProviderDriver]:
    driver_classes = [
        obj
        for _, obj in inspect.getmembers(module, inspect.isclass)
        if obj.__module__ == module.__name__
        and issubclass(obj, ProviderDriver)
        and obj is not ProviderDriver
    ]
    if not driver_classes:
        raise ProviderDefinitionError(
            f"Provider module '{module.__name__}' must define one ProviderDriver implementation."
        )
    if len(driver_classes) > 1:
        raise ProviderDefinitionError(
            f"Provider module '{module.__name__}' defines multiple ProviderDriver implementations."
        )
    return driver_classes[0]


def _validate_driver(driver: ProviderDriver) -> None:
    provider = getattr(driver, "provider", None)
    if provider is None:
        raise ProviderDefinitionError(
            "Provider driver definition must be declared.")
    if not isinstance(provider, ServiceProvider):
        raise ProviderDefinitionError(
            f"Provider driver definition must be a ServiceProvider, got '{type(provider).__name__}'."
        )


class ProviderCatalogImpl(ProviderCatalog):
    def __init__(self, drivers: list[ProviderDriver]) -> None:
        ordered_drivers = sorted(
            drivers, key=lambda item: str(item.provider.name))
        drivers_by_name: dict[ProviderName, ProviderDriver] = {}
        for driver in ordered_drivers:
            name = ProviderName(str(driver.provider.name))
            if name in drivers_by_name:
                raise ProviderDefinitionError(
                    "Provider name must be unique.", provider_name=str(name)
                )
            drivers_by_name[name] = driver

        self._drivers = MappingProxyType(drivers_by_name)
        self._providers = tuple(
            driver.provider for driver in drivers_by_name.values())

    def list_providers(self) -> list[ServiceProvider]:
        return list(self._providers)

    def get_provider(self, name: ProviderName | str) -> ServiceProvider:
        return self.get_driver(name).provider

    def get_driver(self, name: ProviderName | str) -> ProviderDriver:
        normalized_name = ProviderName(str(name))
        try:
            return self._drivers[normalized_name]
        except KeyError as exc:
            raise UnknownProviderError(str(normalized_name)) from exc
