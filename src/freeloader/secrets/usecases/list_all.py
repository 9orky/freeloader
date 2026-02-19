import click

from ._storage import ensure_unlocked, load_storage


def list_all(namespace: str | None = None) -> None:
    storage = load_storage()
    ensure_unlocked(storage)
    for secret in storage.list(namespace):
        click.echo(f"{secret.namespace}/{secret.name}")
