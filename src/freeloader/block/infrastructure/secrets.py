from dataclasses import dataclass, field

from freeloader.secrets import Secrets

from ..domain.repository import SecretsReader


@dataclass(frozen=True)
class SecretsAdapter(SecretsReader):
    secrets: Secrets = field(default_factory=Secrets.for_default_namespace)

    def has_secrets(self, secret_names: list[str]) -> bool:
        return self.secrets.has_secrets(secret_names)

    def read(self, secret_names: list[str]) -> dict[str, str]:
        return self.secrets.read_secrets(secret_names)
