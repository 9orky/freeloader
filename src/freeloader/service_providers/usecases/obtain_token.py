from ..adapters.secrets import write_credentials
from ..adapters import service_providers


def auth_provider(name: str, credentials: dict[str, str]) -> None:
    service_providers.authorize_provider(name, credentials)
    write_credentials(credentials)
