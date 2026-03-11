from .. import application
from ..models import AuthorizationResult, ProviderBillingResult, ServiceProviderInfo


def list_providers() -> list[ServiceProviderInfo]:
    return application.list_providers()


def get_provider(name: str) -> ServiceProviderInfo:
    return application.get_provider(name)


def authorize_provider(name: str, credentials: dict[str, str]) -> AuthorizationResult:
    return application.authorize_provider(name, credentials)


def check_billing(name: str) -> ProviderBillingResult:
    return application.check_billing(name)
