import click
import typer

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


def _run_obtain_steps(steps: list) -> dict[str, str]:
    context: dict[str, str] = {}
    for step in steps:
        match step.action:
            case "input":
                context[step.value] = typer.prompt(step.value)
            case "info":
                console.info(step.value.format(**context))
            case "open_url":
                console.info(f"→ {step.value.format(**context)}")
    return context


@auth_group.command()
@click.argument("name", required=True)
@console.handle_cli_error
def provider(name: str):
    info = usecases.get_provider(name)
    collected = _run_obtain_steps(info.obtain_token_steps)
    remaining = [k for k in info.auth_keys if k not in collected]
    credentials = {**collected, **console.prompter(remaining, True)}
    usecases.auth_provider(name, credentials)
