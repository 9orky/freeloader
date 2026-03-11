from ..adapters.secrets import write_credentials
from ..models import AuthorizationResult
from ..provider.auth import Credentials
from ..provider.registry import load_provider


def auth_provider(name: str, credentials: dict[str, str]) -> AuthorizationResult:
    provider = load_provider(name)
    provider.check_installation()

    if provider.requires_auth:
        provider.check_credentials(Credentials(credentials))
        write_credentials(credentials)
        stored_credentials = sorted(credentials.keys())
    else:
        stored_credentials = []

    return AuthorizationResult(
        provider=name,
        stored_credentials=stored_credentials,
    )


__all__ = ["auth_provider"]
