from pathlib import Path

from .models import Secret, DEFAULT_NAMESPACE
from .session import SecretSession, PasswordRequiredError
from .vault import SecretVault


class SecretNotFoundError(Exception):
    pass


class Storage:
    _VAULT_FILE = "vault"
    _SESSION_FILE = "session"

    def __init__(self, secrets_folder: Path, session_folder: Path) -> None:
        self._session = SecretSession(session_folder / self._SESSION_FILE)
        self._vault_path = secrets_folder / self._VAULT_FILE
        self._vault: SecretVault | None = None

    def _get_vault(self) -> SecretVault:
        if self._vault is None:
            self._vault = SecretVault(self._vault_path, self._session.get_password())
        return self._vault

    def _resolve(self, namespace: str | None) -> str:
        return namespace or DEFAULT_NAMESPACE

    def _assert_exists(self, key: str, namespace: str) -> None:
        if not self._get_vault().has(key, namespace):
            raise SecretNotFoundError(f"Secret '{key}' not found in '{namespace}'")

    def get(self, key: str, namespace: str | None = None) -> Secret:
        ns = self._resolve(namespace)
        self._assert_exists(key, ns)
        return Secret(name=key, value=self._get_vault().get(key, ns), namespace=ns)

    def set(self, key: str, value: str, namespace: str | None = None) -> None:
        ns = self._resolve(namespace)
        self._get_vault().set(key, value, ns)

    def list(self, namespace: str | None = None) -> list[Secret]:
        ns = self._resolve(namespace)
        return [Secret(name=k, value="", namespace=ns) for k in self._get_vault().list(ns)]

    def delete(self, key: str, namespace: str | None = None) -> None:
        ns = self._resolve(namespace)
        self._assert_exists(key, ns)
        self._get_vault().delete(key, ns)

    def has(self, key: str, namespace: str | None = None) -> bool:
        return self._get_vault().has(key, self._resolve(namespace))

    def save_password(self, password: str) -> None:
        self._session.save_password(password)
