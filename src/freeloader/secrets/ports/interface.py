from dataclasses import dataclass

from .. import usecases
from ..usecases._storage import load_storage


@dataclass(frozen=True)
class Secrets:
    namespace: str

    def read_secrets(self, names: list[str]) -> dict[str, str]:
        storage = load_storage()
        return {name: storage.get(name, self.namespace).value for name in names}

    def write_secret(self, name: str, value: str) -> None:
        usecases.write_secret(name, value, self.namespace)

    def has_secrets(self, names: list[str]) -> bool:
        storage = load_storage()
        return all(storage.has(name, self.namespace) for name in names)

    @classmethod
    def for_default_namespace(cls) -> "Secrets":
        return cls(namespace="global")
