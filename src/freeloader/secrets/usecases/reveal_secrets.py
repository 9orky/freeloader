import click

from ._storage import ensure_unlocked, load_storage


def reveal_secrets(namespace: str | None = None) -> None:
    storage = load_storage()
    ensure_unlocked(storage)
    for secret in storage.list(namespace):
        full = storage.get(secret.name, namespace)
        click.echo(f"{full.namespace}/{full.name} = {full.value}")
