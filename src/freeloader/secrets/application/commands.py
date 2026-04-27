from ..infrastructure import load_secret_repository
from ..domain.entity import SecretAvailabilityReport


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


def check_secret_availability(
    names: list[str],
    namespace: str | None = None,
) -> SecretAvailabilityReport:
    storage = load_secret_repository()
    required_keys = tuple(dict.fromkeys(names))
    present_keys = tuple(
        key for key in required_keys if storage.has(key, namespace)
    )
    missing_keys = tuple(
        key for key in required_keys if key not in present_keys
    )
    return SecretAvailabilityReport(
        required_keys=required_keys,
        present_keys=present_keys,
        missing_keys=missing_keys,
    )
