from .. import usecases
from ..usecases._storage import load_storage


def read_secrets(namespace: str, secret_names: list[str]) -> dict[str, str]:
    storage = load_storage()
    return {name: storage.get(name, namespace).value for name in secret_names}


def write_secret(namespace: str, secret_name: str, secret_value: str) -> None:
    usecases.write_secret(secret_name, secret_value, namespace)


def has_secrets(secret_names: list[str], namespace: str | None = None) -> bool:
    storage = load_storage()
    return all(storage.has(name, namespace) for name in secret_names)
