import click
import dotenv
from typer.main import get_command

from .hosts.cli import hosts_app
from .project import project_group
from .secrets import secrets_group
from .service_providers.cli import service_providers_app


def build_app() -> click.Group:
    dotenv.load_dotenv()

    @click.group()
    def root() -> None:
        pass

    root.add_command(get_command(hosts_app), name="hosts")
    root.add_command(project_group)
    root.add_command(secrets_group)
    root.add_command(get_command(service_providers_app),
                     name="service-providers")
    return root


app = build_app()
