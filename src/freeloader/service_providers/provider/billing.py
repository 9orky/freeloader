from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

from freeloader.shared import registry as lazy

from .auth import Credentials


class BillingCheckCost(str, Enum):
    free = "free"
    paid = "paid"


class BillingLineItem(BaseModel):
    service: str
    amount_usd: float
    currency: str = "USD"


class FreeTierUsage(BaseModel):
    service: str
    metric: str
    used: float
    limit: float
    unit: str


class BillingReport(BaseModel):
    provider: str
    total_usd: float
    currency: str = "USD"
    period: str
    items: list[BillingLineItem] = []
    free_tier_usage: list[FreeTierUsage] = []


class BillingAdapter(ABC):
    billing_check_cost: BillingCheckCost

    @abstractmethod
    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...


billing_adapters = lazy.LazyRegistry[BillingAdapter]("BillingAdapterRegistry")


def supports_billing(provider_name: str) -> bool:
    try:
        billing_adapters.get(provider_name)
        return True
    except KeyError:
        return False


def get_billing_check_cost(provider_name: str) -> BillingCheckCost:
    adapter = billing_adapters.get(provider_name)
    return adapter.billing_check_cost


def fetch_billing(provider_name: str, credentials: Credentials) -> BillingReport:
    adapter = billing_adapters.get(provider_name)
    return adapter.fetch_billing(credentials)
