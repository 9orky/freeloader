from pathlib import Path

from freeloader.shared.runtime import Freeloader

from .models import Secret, DEFAULT_NAMESPACE
from .session import SecretSession, PasswordRequiredError as PasswordRequiredError
from .vault import SecretVault

__all__ = [
    "DEFAULT_NAMESPACE",
    "load_storage",
    "PasswordRequiredError",
    "Secret",
    "SecretNotFoundError",
    "SecretSession",
    "Storage",
]


class SecretNotFoundError(Exception):
    pass


def load_storage(password: str | None = None, cwd: Path | None = None) -> "Storage":
    runtime = Freeloader.from_env(cwd or Path.cwd())
    storage = Storage(runtime.home_folder,
                      runtime.secrets_folder, runtime.session_folder)
    storage.ensure_unlocked(password)
    return storage


class Storage:
    _VAULT_FILE = "vault"
    _SESSION_FILE = "session"
    _PASSWORD_FILE = "vault-password"

    def __init__(self, home_folder: Path, secrets_folder: Path, session_folder: Path) -> None:
        self._session = SecretSession(
            home_folder / self._PASSWORD_FILE,
            legacy_file_paths=(session_folder / self._SESSION_FILE,),
        )
        self._vault_path = secrets_folder / self._VAULT_FILE
        self._vault: SecretVault | None = None

    def _get_vault(self) -> SecretVault:
        if self._vault is None:
            self._vault = SecretVault(
                self._vault_path, self._session.get_password())
        return self._vault

    def _resolve(self, namespace: str | None) -> str:
        return namespace or DEFAULT_NAMESPACE

    def _assert_exists(self, key: str, namespace: str) -> None:
        if not self._get_vault().has(key, namespace):
            raise SecretNotFoundError(
                f"Secret '{key}' not found in '{namespace}'")

    def get(self, key: str, namespace: str | None = None) -> Secret:
        ns = self._resolve(namespace)
        self._assert_exists(key, ns)
        return Secret(name=key, value=self._get_vault().get(key, ns), namespace=ns)

    def set(self, key: str, value: str, namespace: str | None = None) -> None:
        ns = self._resolve(namespace)
        self._get_vault().set(key, value, ns)

    def set_many(self, values: dict[str, str], namespace: str | None = None) -> None:
        if not values:
            return
        ns = self._resolve(namespace)
        self._get_vault().set_many(values, ns)

    def list(self, namespace: str | None = None) -> list[Secret]:
        ns = self._resolve(namespace)
        return [Secret(name=k, value="", namespace=ns) for k in self._get_vault().list(ns)]

    def delete(self, key: str, namespace: str | None = None) -> None:
        ns = self._resolve(namespace)
        self._assert_exists(key, ns)
        self._get_vault().delete(key, ns)

    def has(self, key: str, namespace: str | None = None) -> bool:
        return self._get_vault().has(key, self._resolve(namespace))

    def ensure_unlocked(self, password: str | None = None) -> None:
        try:
            self.has("__probe__", "__probe__")
        except PasswordRequiredError:
            if password is None:
                raise
            self.save_password(password)

    def save_password(self, password: str) -> None:
        self._session.save_password(password)
