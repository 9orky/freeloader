from dataclasses import dataclass

from .. import usecases
from ..usecases._storage import load_storage


@dataclass(frozen=True)
class Secrets:
    namespace: str

    def read_secrets(self, names: list[str]) -> dict[str, str]:
        storage = load_storage()
        normalized_names = [self._normalize_name(name) for name in names]
        return {name: storage.get(name, self.namespace).value for name in normalized_names}

    def write_secret(self, name: str, value: str) -> None:
        normalized_name = self._normalize_name(name)
        usecases.write_secret(normalized_name, value, self.namespace)

    def has_secrets(self, names: list[str]) -> bool:
        storage = load_storage()
        normalized_names = [self._normalize_name(name) for name in names]
        return all(storage.has(name, self.namespace) for name in normalized_names)
    
    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    @classmethod
    def for_default_namespace(cls) -> "Secrets":
        return cls(namespace="global")
