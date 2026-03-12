from dataclasses import dataclass

from ..application import commands, queries
from ..domain.entity import DEFAULT_NAMESPACE


@dataclass(frozen=True)
class Secrets:
    namespace: str

    def read_secrets(self, names: list[str]) -> dict[str, str]:
        normalized_names = [self._normalize_name(name) for name in names]
        return queries.read_secrets(normalized_names, self.namespace)

    def write_secret(self, name: str, value: str) -> None:
        normalized_name = self._normalize_name(name)
        commands.write_secret(normalized_name, value, self.namespace)

    def write_secrets(self, values: dict[str, str]) -> None:
        normalized_values = {
            self._normalize_name(name): value
            for name, value in values.items()
        }
        
        commands.write_secrets(normalized_values, self.namespace)

    def has_secrets(self, names: list[str]) -> bool:
        normalized_names = [self._normalize_name(name) for name in names]
        return commands.has_secrets(normalized_names, self.namespace)

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    @classmethod
    def for_default_namespace(cls) -> "Secrets":
        return cls(namespace=DEFAULT_NAMESPACE)
