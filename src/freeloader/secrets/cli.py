import typer

from freeloader.shared import console

from . import application


secrets_app = typer.Typer(
    name="secrets",
    help="Manage stored secrets",
    no_args_is_help=True,
)


@secrets_app.command("ls", help="List secret names")
@console.handle_errors
def list_secret_names(
    namespace: str | None = typer.Option(None, "--namespace", "-n"),
) -> None:
    for secret in application.list_secrets(namespace):
        typer.echo(f"{secret.namespace}/{secret.name}")


@secrets_app.command(help="Show stored secret values")
@console.handle_errors
def reveal(
    namespace: str | None = typer.Option(None, "--namespace", "-n"),
) -> None:
    for secret in application.reveal_secrets(namespace):
        typer.echo(f"{secret.namespace}/{secret.name} = {secret.value}")


@secrets_app.command(help="Store a secret value")
@console.handle_errors
def add(
    key: str = typer.Argument(..., help="Secret key"),
    namespace: str | None = typer.Option(None, "--namespace", "-n"),
) -> None:
    value = typer.prompt(f"Value for secret '{key}'", hide_input=True)
    result = application.write_secret(key, value, namespace)
    typer.echo(f"Secret '{result.name}' written.")


@secrets_app.command(help="Remove a stored secret")
@console.handle_errors
def remove(
    key: str = typer.Argument(..., help="Secret key"),
    namespace: str | None = typer.Option(None, "--namespace", "-n"),
) -> None:
    result = application.remove_secret(key, namespace)
    typer.echo(f"Secret '{result.name}' removed.")
