import click

from freeloader.shared import console
from .. import usecases


@click.group(name="secrets")
def secrets_group():
    pass


@secrets_group.command()
@click.option("--namespace", "-n", required=False)
@console.handle_cli_error
def ls(namespace: str | None):
    usecases.list_all(namespace)


@secrets_group.command()
@click.option("--namespace", "-n", required=False)
@console.handle_cli_error
def reveal(namespace: str | None):
    usecases.reveal_secrets(namespace)


@secrets_group.command()
@click.argument("key", required=True)
@click.option("--namespace", "-n", required=False)
@console.handle_cli_error
def add(key: str, namespace: str | None):
    value = click.prompt(f"Value for secret '{key}'", hide_input=True)
    usecases.write_secret(key, value, namespace)


@secrets_group.command()
@click.argument("key", required=True)
@click.option("--namespace", "-n", required=False)
@console.handle_cli_error
def remove(key: str, namespace: str | None):
    usecases.remove_secret(key, namespace)
