import os
from pathlib import Path
import click

from freeloader.shared.console import handle_cli_error
from freeloader.shared.runtime import Freeloader

from .. import usecases


@click.group(name="project")
def project_group():
    Freeloader().must_be_installed()


@project_group.command()
@handle_cli_error
def ls():
    all_projects = usecases.list_all_projects()
    if len(all_projects) == 0:
        click.secho("No projects registered yet.", fg="yellow", bold=True)
        return 0

    click.echo("Registered projects:\n")
    for project in all_projects:
        click.secho(f"- {project['name']} ({project['path']})", fg="cyan")


@project_group.command()
@handle_cli_error
def init():
    project_path = Path(os.getcwd())
    usecases.initialize_project(project_path.name, project_path)
    click.secho(
        f"\nProject '{project_path.name}' initialized!\n", fg="green", bold=True)


@project_group.command()
@handle_cli_error
def provision():
    project_path = Path(os.getcwd())
    usecases.provision_project(project_path)


@project_group.command()
@handle_cli_error
def destroy():
    project_path = Path(os.getcwd())
    usecases.destroy_project(project_path)
    click.secho(
        f"\nProject '{project_path.name}' destroyed successfully!\n", fg="red", bold=True)
