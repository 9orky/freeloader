from ..infrastructure import load_secret_repository


def write_secret(
    key: str,
    value: str,
    namespace: str | None = None,
) -> None:
    storage = load_secret_repository()
    storage.store(key, value, namespace)


def write_secrets(
    values: dict[str, str],
    namespace: str | None = None,
) -> None:
    load_secret_repository().store_many(values, namespace)


def remove_secret(
    key: str,
    namespace: str | None = None,
) -> None:
    storage = load_secret_repository()
    storage.delete(key, namespace)


def has_secrets(
    names: list[str],
    namespace: str | None = None,
) -> bool:
    storage = load_secret_repository()
    return all(storage.has(name, namespace) for name in names)
