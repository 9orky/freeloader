from .models import SecretEntry, SecretMutationResult
from .storage import load_storage


def list_secrets(namespace: str | None = None) -> list[SecretEntry]:
    return load_storage().list(namespace)


def reveal_secrets(namespace: str | None = None) -> list[SecretEntry]:
    storage = load_storage()
    return [storage.get(secret.name, namespace) for secret in storage.list(namespace)]


def read_secrets(
    names: list[str],
    namespace: str | None = None,
) -> dict[str, str]:
    storage = load_storage()
    return {name: storage.get(name, namespace).value for name in names}


def write_secret(
    key: str,
    value: str,
    namespace: str | None = None,
) -> SecretMutationResult:
    storage = load_storage()
    storage.set(key, value, namespace)
    return SecretMutationResult(name=key)


def write_secrets(
    values: dict[str, str],
    namespace: str | None = None,
) -> None:
    load_storage().set_many(values, namespace)


def remove_secret(
    key: str,
    namespace: str | None = None,
) -> SecretMutationResult:
    storage = load_storage()
    storage.delete(key, namespace)
    return SecretMutationResult(name=key)


def has_secrets(
    names: list[str],
    namespace: str | None = None,
) -> bool:
    storage = load_storage()
    return all(storage.has(name, namespace) for name in names)
