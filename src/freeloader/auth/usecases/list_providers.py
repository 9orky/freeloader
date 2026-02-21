from dataclasses import dataclass

from ..adapters import service_providers


@dataclass
class ProviderInfo:
    name: str
    requires_auth: bool
    requires_tech_stack: bool
    auth_keys: list[str]


def list_providers() -> list[ProviderInfo]:
    providers = service_providers.find_all()
    return [ProviderInfo(
        name=str(provider["name"]),
        requires_auth=bool(provider["requires_auth"]),
        requires_tech_stack=bool(provider["requires_tech_stack"]),
        auth_keys=list(provider["auth_keys"]),
    ) for provider in providers]