from dataclasses import dataclass, field

from freeloader.credentials.vault import SecretVault


@dataclass(frozen=True)
class SecretResult:
    success: bool
    key: str = ""
    value: str = ""
    keys: list[str] = field(default_factory=list)
    error: str = ""


class SecretUseCases:
    def __init__(self, vault: SecretVault) -> None:
        self._vault = vault

    def set(self, key: str, value: str) -> SecretResult:
        self._vault.set(key, value)
        return SecretResult(success=True, key=key)

    def get(self, key: str) -> SecretResult:
        try:
            value = self._vault.get(key)
            return SecretResult(success=True, key=key, value=value)
        except KeyError:
            return SecretResult(success=False, key=key, error=f"Secret '{key}' not found")

    def list(self) -> SecretResult:
        keys = self._vault.list()
        return SecretResult(success=True, keys=keys)

    def delete(self, key: str) -> SecretResult:
        try:
            self._vault.delete(key)
            return SecretResult(success=True, key=key)
        except KeyError:
            return SecretResult(success=False, key=key, error=f"Secret '{key}' not found")
