from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import ProviderDefinitionError
from .value_object import ProviderName


class BillingCheckCost(str, Enum):
    free = "free"
    paid = "paid"


@dataclass(frozen=True)
class BillingLineItem:
    service: str
    amount_usd: float
    currency: str = "USD"

    def __post_init__(self) -> None:
        if not self.service.strip():
            raise ProviderDefinitionError(
                "Billing line items must declare a service name.")
        if not self.currency.strip():
            raise ProviderDefinitionError(
                "Billing line items must declare a currency.")


@dataclass(frozen=True)
class FreeTierUsage:
    service: str
    metric: str
    used: float
    limit: float
    unit: str

    def __post_init__(self) -> None:
        if not self.service.strip():
            raise ProviderDefinitionError(
                "Free tier usage must declare a service name.")
        if not self.metric.strip():
            raise ProviderDefinitionError(
                "Free tier usage must declare a metric.")
        if not self.unit.strip():
            raise ProviderDefinitionError(
                "Free tier usage must declare a unit.")


@dataclass(frozen=True)
class BillingReport:
    provider: ProviderName | str
    total_usd: float
    period: str
    currency: str = "USD"
    items: tuple[BillingLineItem, ...] = ()
    free_tier_usage: tuple[FreeTierUsage, ...] = ()

    def __post_init__(self) -> None:
        provider = ProviderName(str(self.provider))
        if not self.period.strip():
            raise ProviderDefinitionError(
                "Billing report period must be non-empty.", provider_name=str(provider))
        if not self.currency.strip():
            raise ProviderDefinitionError(
                "Billing report currency must be non-empty.", provider_name=str(provider))

        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "items", tuple(self.items))
        object.__setattr__(self, "free_tier_usage",
                           tuple(self.free_tier_usage))


@dataclass(frozen=True)
class BillingSpec:
    check_cost: BillingCheckCost | str

    def __post_init__(self) -> None:
        try:
            check_cost = self.check_cost if isinstance(
                self.check_cost, BillingCheckCost) else BillingCheckCost(self.check_cost)
        except ValueError as exc:
            raise ProviderDefinitionError(
                f"Invalid billing check cost '{self.check_cost}'.") from exc
        object.__setattr__(self, "check_cost", check_cost)
