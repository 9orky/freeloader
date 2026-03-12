from freeloader import fl

from ..domain.repository import SecretRepository
from .session import SecretSession
from .vault import SecretVault


def load_secret_repository(passphrase: str | None = None) -> SecretRepository:
    session = SecretSession(fl.session_folder)
    password = session.get_password() if passphrase is None else passphrase
    return SecretVault(fl.secrets_folder, str(password))


__all__ = [
    "load_secret_repository",
]
