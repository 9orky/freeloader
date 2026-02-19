import click

from .shared.system import Freeloader
from .project.ports.cli import project_group
from .secrets.ports.cli import secrets_group


@click.group()
def app():
    pass


app.add_command(project_group)
app.add_command(secrets_group)


@app.command()
def install():
    try:
        Freeloader().install()
        click.echo("Freeloader has been installed successfully.")
    except AssertionError as e:
        click.echo(str(e))
