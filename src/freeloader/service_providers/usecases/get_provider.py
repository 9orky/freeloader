from ._views_auth import ProviderView, ObtainTokenStepView
from ..adapters import service_providers


def get_provider(name: str) -> ProviderView:
    provider = service_providers.get(name)

    return ProviderView(
        name=str(provider["name"]),
        requires_auth=bool(provider["requires_auth"]),
        requires_tech_stack=bool(provider["requires_tech_stack"]),
        auth_keys=list(provider["auth_keys"]
                       ) if provider["auth_keys"] is not None else [],
        obtain_token_steps=[
            ObtainTokenStepView(action=s.action, value=s.value)
            for s in provider["obtain_token_steps"]
            if provider["obtain_token_steps"] is not None
        ],
    )
