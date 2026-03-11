from ..models import ServiceProviderInfo
from ..provider.registry import load_all_providers
from .get_provider import get_provider


def list_providers() -> list[ServiceProviderInfo]:
    providers = [get_provider(name) for name in load_all_providers()]
    return sorted(providers, key=lambda provider: provider.name)


__all__ = ["list_providers"]
