import json
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..domain import DEFAULT_NAMESPACE
from ..domain.entity import Secret
from ..domain.repository import SecretRepository


_VAULT_FILE = "vault"


class SecretVault(SecretRepository):
    def __init__(self, vault_folder: Path, passphrase: str) -> None:
        assert vault_folder.is_dir(), f"Provided vault folder path '{vault_folder}' is not a directory"

        self._path = vault_folder / _VAULT_FILE
        self._fernet = self._derive_fernet(passphrase)
        self._data: dict[str, dict[str, str]] = self._load()

    def _derive_fernet(self, passphrase: str) -> Fernet:
        salt = b"freeloader-vault-salt-v1"
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                         salt=salt, iterations=480_000)
        key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
        return Fernet(key)

    def _load(self) -> dict[str, dict[str, str]]:
        if not self._path.exists():
            return {}
        encrypted = self._path.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        plaintext = json.dumps(self._data).encode()
        self._path.write_bytes(self._fernet.encrypt(plaintext))

    def _resolve_namespace(self, namespace: str | None) -> str:
        return namespace if namespace is not None else DEFAULT_NAMESPACE

    def get(self, key: str, namespace: str | None = None) -> Secret:
        namespace = self._resolve_namespace(namespace)
        return Secret(name=key, value=self._data[namespace][key])

    def store(self, key: str, value: str, namespace: str | None = None) -> None:
        namespace = self._resolve_namespace(namespace)
        self._data.setdefault(namespace, {})[key] = value
        self._save()

    def store_many(self, values: dict[str, str], namespace: str | None = None) -> None:
        namespace = self._resolve_namespace(namespace)
        self._data.setdefault(namespace, {}).update(values)
        self._save()

    def find(self, namespace: str | None = None) -> list[Secret]:
        namespace = self._resolve_namespace(namespace)
        return [
            Secret(name=key, value=value) 
            for key, value in self._data.get(namespace, {}).items()
        ]

    def delete(self, key: str, namespace: str | None = None) -> None:
        namespace = self._resolve_namespace(namespace)
        del self._data[namespace][key]
        self._save()

    def has(self, key: str, namespace: str | None = None) -> bool:
        namespace = self._resolve_namespace(namespace)
        return namespace in self._data and key in self._data[namespace]
