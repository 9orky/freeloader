import click

from freeloader import console
from .. import usecases


@click.group(name="auth")
def auth_group():
    pass


@auth_group.command()
def ls():
    providers = usecases.list_providers()
    headers = ["Name", "Requires Auth", "Requires Tech Stack"]

    rows = [[
        provider.name,
        provider.requires_auth,
        provider.requires_tech_stack
    ] for provider in providers]

    console.print_table("Installed Providers", headers, rows)


@auth_group.command()
@click.argument("name", required=True)
@console.handle_cli_error
def provider(name: str):
    provider = usecases.get_provider(name)
    credentials = console.prompter(provider.auth_keys, True)
    usecases.auth_provider(name, credentials)
