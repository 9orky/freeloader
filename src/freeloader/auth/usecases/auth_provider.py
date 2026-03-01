from freeloader.secrets import Secrets

from ..adapters import service_providers


def auth_provider(name: str, credentials: dict[str, str]) -> None:
    service_providers.authorize_provider(name, credentials)
    secrets = Secrets.for_default_namespace()
    
    for key, value in credentials.items():
        secrets.write_secret(key, value)
