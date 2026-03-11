from dataclasses import dataclass

from .storage.models import Secret

SecretEntry = Secret


@dataclass(frozen=True)
class SecretMutationResult:
    name: str
