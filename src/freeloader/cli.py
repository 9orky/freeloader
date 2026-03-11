import click

from .project import project_group
from .secrets import secrets_group


@click.group()
def app():
    pass


app.add_command(auth_group)
app.add_command(billing_group)
app.add_command(project_group)
app.add_command(secrets_group)
