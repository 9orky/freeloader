import importlib

from freeloader.shared import registry as lazy

from .auth import ServiceProvider


providers = lazy.LazyRegistry[ServiceProvider]("ServiceProviderRegistry")

_BOOTSTRAPPED = False
_PROVIDER_PACKAGES = ("aws", "coolify", "docker", "git", "github", "gitlab")


def ensure_provider_registrations_loaded() -> None:
    global _BOOTSTRAPPED

    if _BOOTSTRAPPED:
        return

    for package_name in _PROVIDER_PACKAGES:
        importlib.import_module(f"{__package__}.{package_name}")

    _BOOTSTRAPPED = True


def load_all_providers() -> dict[str, ServiceProvider]:
    ensure_provider_registrations_loaded()
    return providers.find_all()


def load_provider(name: str) -> ServiceProvider:
    ensure_provider_registrations_loaded()
    return providers.get(name)
