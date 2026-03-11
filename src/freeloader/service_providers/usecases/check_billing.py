from ..adapters import ServiceProviderBillingAdapter


def check_provider(name: str) -> None:
    adapter = ServiceProviderBillingAdapter()
    adapter.check_provider(name)
    print(f"Billing report for {name}: ", value)
