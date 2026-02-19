from pathlib import Path

from .models import Secret, DEFAULT_NAMESPACE
from .session import SecretSession, PasswordRequiredError
from .vault import SecretVault

class SecretNotFoundError(Exception):
    pass

class Storage:
    def __init__(self, vault_path: Path, session_path: Path) -> None:
        self._vault_path = vault_path
        self._session = SecretSession(session_path)
        self._vault: SecretVault | None = None

    def _get_vault(self) -> SecretVault:
        if self._vault is None:
            self._vault = SecretVault(self._vault_path, self._session.get_password())
        return self._vault
    
    def _assert_exists(self, key: str, namespace: str) -> None:
        if not self._get_vault().has(key, namespace):
            raise SecretNotFoundError(f"Secret '{key}' not found in namespace '{namespace}'")

    def get(self, key: str, namespace: str = DEFAULT_NAMESPACE) -> Secret:
        self._assert_exists(key, namespace)
        return Secret(name=key, value=self._get_vault().get(key, namespace), namespace=namespace)

    def set(self, secret: Secret) -> None:
        self._get_vault().set(secret.name, secret.value, secret.namespace)

    def list(self, namespace: str = DEFAULT_NAMESPACE) -> list[Secret]:
        return [Secret(name=k, value="", namespace=namespace) for k in self._get_vault().list(namespace)]

    def delete(self, key: str, namespace: str = DEFAULT_NAMESPACE) -> None:
        self._assert_exists(key, namespace)
        self._get_vault().delete(key, namespace)

    def has(self, key: str, namespace: str = DEFAULT_NAMESPACE) -> bool:
        return self._get_vault().has(key, namespace)

    def save_password(self, password: str) -> None:
        self._session.save_password(password)
