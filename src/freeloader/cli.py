import os
from pathlib import Path
from typing import Annotated

import typer

from freeloader import __version__
from freeloader.credentials.cli import credentials_app
from freeloader.hosts.cli import hosts_app
from freeloader.pipeline.cli import pipeline_app
from freeloader.projects.cli import projects_app
from freeloader.shared.errors import handle_errors


app = typer.Typer(
    name="fl",
    no_args_is_help=True,
    help="Freeloader CLI",
)
app.add_typer(credentials_app)
app.add_typer(hosts_app)
app.add_typer(pipeline_app)
app.add_typer(projects_app)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"freeloader {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[bool, typer.Option(
        "--version", callback=_version_callback, is_eager=True)] = False,
) -> None:
    pass


@app.command(help="SSH into a registered host")
@handle_errors
def ssh(alias: str = typer.Argument(..., help="Host alias from inventory")) -> None:
    from freeloader.factory import Factory

    entry = Factory().hosts.usecases()._store.get(alias)
    if not entry:
        typer.echo(
            f"Host '{alias}' not found. Run 'fl hosts list' to see available hosts.", err=True)
        raise typer.Exit(1)

    key_path = Path(entry.identity_file).expanduser()
    cmd = [
        "ssh",
        "-i", str(key_path),
        "-p", str(entry.port),
        f"{entry.user}@{entry.host}",
    ]
    os.execvp("ssh", cmd)
