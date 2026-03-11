import json
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class SecretVault:
    def __init__(self, path: Path, passphrase: str) -> None:
        self._path = path
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

    def get(self, key: str, namespace: str) -> str:
        return self._data[namespace][key]

    def set(self, key: str, value: str, namespace: str) -> None:
        self._data.setdefault(namespace, {})[key] = value
        self._save()

    def set_many(self, values: dict[str, str], namespace: str) -> None:
        self._data.setdefault(namespace, {}).update(values)
        self._save()

    def list(self, namespace: str) -> list[str]:
        return list(self._data.get(namespace, {}).keys())

    def delete(self, key: str, namespace: str) -> None:
        del self._data[namespace][key]
        self._save()

    def has(self, key: str, namespace: str) -> bool:
        return namespace in self._data and key in self._data[namespace]
