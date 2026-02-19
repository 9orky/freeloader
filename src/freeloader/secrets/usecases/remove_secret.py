import click

from ._storage import ensure_unlocked, load_storage


def remove_secret(key: str, namespace: str | None = None) -> None:
    storage = load_storage()
    ensure_unlocked(storage)
    storage.delete(key, namespace)
    click.echo(f"Secret '{key}' removed.")
