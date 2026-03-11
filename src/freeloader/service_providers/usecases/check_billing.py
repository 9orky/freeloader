from ..adapters.secrets import read_credentials
from ..models import ProviderBillingResult
from ..provider.auth import Credentials
from ..provider.billing import fetch_billing
from .get_provider import get_provider


def check_billing(name: str) -> ProviderBillingResult:
    provider_info = get_provider(name)
    if not provider_info.supports_billing:
        raise ValueError(f"Provider '{name}' does not support billing checks")

    credentials = read_credentials(
        provider_info.auth_keys) if provider_info.auth_keys else {}
    report = fetch_billing(name, Credentials(credentials))
    return ProviderBillingResult(
        provider=name,
        billing_check_cost=provider_info.billing_check_cost,
        report=report,
    )


__all__ = ["check_billing"]
