import click

from ._storage import ensure_unlocked, load_storage


def write_secret(key: str, value: str, namespace: str | None = None) -> None:
    storage = load_storage()
    ensure_unlocked(storage)
    storage.set(key, value, namespace)
    click.echo(f"Secret '{key}' written.")
