from .models import AuthorizationResult, ProviderBillingResult, ServiceProviderInfo
from .usecases.auth_provider import auth_provider as authorize_provider_usecase
from .usecases.check_billing import check_billing as check_billing_usecase
from .usecases.get_provider import get_provider as get_provider_usecase
from .usecases.list_providers import list_providers as list_providers_usecase


def list_providers() -> list[ServiceProviderInfo]:
    return list_providers_usecase()


def get_provider(name: str) -> ServiceProviderInfo:
    return get_provider_usecase(name)


def authorize_provider(
    name: str,
    credentials: dict[str, str],
) -> AuthorizationResult:
    return authorize_provider_usecase(name, credentials)


def check_billing(name: str) -> ProviderBillingResult:
    return check_billing_usecase(name)
