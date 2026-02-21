from ._model import ProviderInfo
from ..adapters import service_providers, write_secret


def auth_provider(name: str, credentials: dict[str, str]) -> None:
    service_providers.authorize_provider(name, credentials)
    for key, value in credentials.items():
        write_secret("global", key, value)
