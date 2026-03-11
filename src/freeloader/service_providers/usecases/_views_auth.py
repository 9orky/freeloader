from dataclasses import dataclass


@dataclass
class ObtainTokenStepView:
    action: str
    value: str


@dataclass
class ProviderView:
    name: str
    requires_auth: bool
    requires_tech_stack: bool
    auth_keys: list[str]
    obtain_token_steps: list[ObtainTokenStepView]
