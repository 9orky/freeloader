import dotenv
import typer

from .project import project_app
from .secrets import secrets_app
from .service_providers.cli import service_providers_app


def build_app() -> typer.Typer:
    dotenv.load_dotenv()

    root = typer.Typer()
    root.add_typer(project_app, name="project")
    root.add_typer(secrets_app, name="secrets")
    root.add_typer(service_providers_app, name="service-providers")

    return root


app = build_app()
