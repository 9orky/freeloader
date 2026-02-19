from dataclasses import dataclass, field
from pathlib import Path

from .vault import SecretVault


@dataclass(frozen=True)
class SecretValue:
    value: str


@dataclass(frozen=True)
class Secret:
    key: str
    namespace: str


class SecretUseCases:
    def __init__(self, vault_path: Path, passphrase: str) -> None:
        self._vault = SecretVault(vault_path, passphrase)

    def add_secret(self, key: str, value: str, namespace: str) -> Secret:
        self._vault.set(key, value, namespace)
        return Secret(key=key, namespace=namespace)

    def list_secrets(self, namespace: str) -> Secret:
        keys = self._vault.list(namespace)
        return Secret(key="", namespace=namespace)
    
    def reveal(self, key: str, namespace: str) -> SecretValue:
        value = self._vault.get(key, namespace)
        return SecretValue(value=value)
    
    def reveal_secrets(self, keys: list[str], namespace: str) -> dict[str, SecretValue]:
        return {k: SecretValue(value=self._vault.get(k, namespace)) for k in keys}

    def delete_secret(self, key: str, namespace: str) -> None:
        self._vault.delete(key, namespace)
