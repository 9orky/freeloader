from ..infrastructure import load_secret_repository
from ..domain.entity import Secret


def list_secrets(namespace: str | None = None) -> list[Secret]:
    return load_secret_repository().find(namespace)


def reveal_secrets(namespace: str | None = None) -> list[Secret]:
    storage = load_secret_repository()
    return [storage.get(secret.name, namespace) for secret in storage.find(namespace)]


def read_secrets(
    names: list[str],
    namespace: str | None = None,
) -> dict[str, str]:
    storage = load_secret_repository()
    return {name: storage.get(name, namespace).value for name in names}
