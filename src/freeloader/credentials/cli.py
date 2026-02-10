import typer

from freeloader.factory import Factory
from freeloader.shared.console import error, info, print_table, success
from freeloader.shared.errors import handle_errors


credentials_app = typer.Typer(
    name="credentials",
    help="Manage secrets and provider credentials",
    no_args_is_help=True,
)


@credentials_app.command("set", help="Store a secret in the vault")
@handle_errors
def secrets_set(
    key: str = typer.Argument(..., help="Secret key"),
    value: str = typer.Argument(None, help="Secret value"),
) -> None:
    if value is None:
        value = typer.prompt("Value", hide_input=True)
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    result = Factory(passphrase).credentials.secret_usecases().set(key, value)
    success(f"Secret '{result.key}' saved")


@credentials_app.command("get", help="Read a secret from the vault")
@handle_errors
def secrets_get(key: str = typer.Argument(..., help="Secret key")) -> None:
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    result = Factory(passphrase).credentials.secret_usecases().get(key)
    if result.success:
        typer.echo(result.value)
    else:
        typer.echo(result.error, err=True)
        raise typer.Exit(1)


@credentials_app.command("list-secrets", help="List stored secret keys")
@handle_errors
def secrets_list() -> None:
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    result = Factory(passphrase).credentials.secret_usecases().list()
    if not result.keys:
        info("No secrets stored")
        return
    print_table("Secrets", ["Key"], [[k] for k in sorted(result.keys)])


@credentials_app.command("delete", help="Delete a secret from the vault")
@handle_errors
def secrets_delete(key: str = typer.Argument(..., help="Secret key")) -> None:
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    result = Factory(passphrase).credentials.secret_usecases().delete(key)
    if result.success:
        success(f"Secret '{result.key}' deleted")
    else:
        typer.echo(result.error, err=True)
        raise typer.Exit(1)


@credentials_app.command("add-provider", help="Store provider credentials")
@handle_errors
def providers_add(
    name: str = typer.Argument(...,
                               help="Provider name (github, gitlab, aws, coolify)"),
) -> None:
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    uc = Factory(passphrase).credentials.provider_usecases()

    req = uc.list_required_secrets(name)
    if not req.required:
        error(f"No blocks found for provider '{name}'")
        raise typer.Exit(1)

    values = {key: typer.prompt(key, hide_input=True)
              for key in req.missing_keys}
    result = uc.add(name, values)

    for k in result.already_present:
        info(f"✓ {k} already in vault")
    for k in result.stored_keys:
        success(f"{k} saved")
    if result.credential_status.valid:
        success(f"Authenticated: {result.credential_status.identity}")
    else:
        error(f"Validation failed: {result.credential_status.error}")
    success(f"Provider '{name}' configured")


@credentials_app.command("check", help="Check provider credentials")
@handle_errors
def providers_check() -> None:
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    result = Factory(passphrase).credentials.provider_usecases().check()
    rows = [[r.provider, "✓" if r.valid else "✗", r.detail]
            for r in result.rows]
    print_table("Provider Credentials", ["Provider", "Status", "Detail"], rows)


@credentials_app.command("list-providers", help="List providers and required secrets")
@handle_errors
def providers_list() -> None:
    passphrase = typer.prompt("Vault passphrase", hide_input=True)
    result = Factory(passphrase).credentials.provider_usecases().list()
    if not result.providers:
        info("No providers found")
        return
    rows = [
        [p.provider, ", ".join(
            f"{'✓' if ok else '✗'} {k}" for k, ok in p.secrets)]
        for p in result.providers
    ]
    print_table("Providers", ["Provider", "Secrets"], rows)
