from freeloader.shared import registry as lazy

from .auth import ServiceProvider


providers = lazy.LazyRegistry[ServiceProvider]("ServiceProviderRegistry")


def load_all_providers() -> dict[str, ServiceProvider]:
    return providers.find_all()


def load_provider(name: str) -> ServiceProvider:
    return providers.get(name)
