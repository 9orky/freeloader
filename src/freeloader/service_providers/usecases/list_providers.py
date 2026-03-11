from ._views_auth import ProviderView
from ..adapters import service_providers


def list_providers() -> list[ProviderView]:
    providers = service_providers.find_all()
    return [ProviderView(
        name=str(provider["name"]),
        requires_auth=bool(provider["requires_auth"]),
        requires_tech_stack=bool(provider["requires_tech_stack"]),
        auth_keys=list(provider["auth_keys"]),
    ) for provider in providers]
