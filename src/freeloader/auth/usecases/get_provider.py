from ._model import ProviderInfo
from ..adapters import service_providers


def get_provider(name: str) -> ProviderInfo:
    provider = service_providers.get(name)
    
    return ProviderInfo(
        name=str(provider["name"]),
        requires_auth=bool(provider["requires_auth"]),
        requires_tech_stack=bool(provider["requires_tech_stack"]),
        auth_keys=list(provider["auth_keys"]),
    )