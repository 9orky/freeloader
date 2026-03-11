from ..models import ObtainTokenStepInfo, ServiceProviderInfo
from ..provider.billing import get_billing_check_cost, supports_billing
from ..provider.registry import load_provider


def get_provider(name: str) -> ServiceProviderInfo:
    provider = load_provider(name)
    has_billing = supports_billing(name)
    billing_check_cost = get_billing_check_cost(name) if has_billing else None

    return ServiceProviderInfo(
        name=name,
        requires_auth=provider.requires_auth,
        requires_tech_stack=provider.requires_tech_stack,
        auth_keys=list(provider.auth_keys or []),
        obtain_token_steps=[
            ObtainTokenStepInfo(action=step.action, value=step.value)
            for step in provider.obtain_token_steps or []
        ],
        supports_billing=has_billing,
        billing_check_cost=billing_check_cost,
    )


__all__ = ["get_provider"]
