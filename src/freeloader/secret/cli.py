import click

from freeloader.shared.errors import handle_errors
from .use_cases import SecretUseCases


@click.group(name="secrets")
def secrets_group():
    """Manage secrets and provider credentials."""
    pass


@secrets_group.command(name="set")
@click.argument("key")
@click.argument("value", required=False)
@handle_errors
def secrets_set(key, value):
    """Store a secret in the vault."""
    pass


@secrets_group.command(name="get")
@click.argument("key")
@handle_errors
def secrets_get(key):
    """Read a secret from the vault."""
    pass


@secrets_group.command(name="list")
@handle_errors
def secrets_list():
    """List stored secret keys."""
    pass
