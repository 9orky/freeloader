from dataclasses import dataclass

from .provider.billing import BillingCheckCost, BillingReport


@dataclass(frozen=True)
class ObtainTokenStepInfo:
    action: str
    value: str


@dataclass(frozen=True)
class ServiceProviderInfo:
    name: str
    requires_auth: bool
    requires_tech_stack: bool
    auth_keys: list[str]
    obtain_token_steps: list[ObtainTokenStepInfo]
    supports_billing: bool
    billing_check_cost: BillingCheckCost | None = None


@dataclass(frozen=True)
class AuthorizationResult:
    provider: str
    stored_credentials: list[str]


@dataclass(frozen=True)
class ProviderBillingResult:
    provider: str
    billing_check_cost: BillingCheckCost | None
    report: BillingReport | None
