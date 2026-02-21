from dataclasses import dataclass


@dataclass
class ProviderInfo:
    name: str
    requires_auth: bool
    requires_tech_stack: bool
    auth_keys: list[str]
