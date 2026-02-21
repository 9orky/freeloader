import functools

import typer
from rich.console import Console
from rich.table import Table

_console = Console()
_err_console = Console(stderr=True)


def info(message: str) -> None:
    _console.print(message, style="dim")


def ok(message: str) -> None:
    _console.print(f"✓ {message}", style="green")


def warn(message: str) -> None:
    _console.print(f"⚠ {message}", style="yellow")


def error(message: str) -> None:
    _err_console.print(f"✗ {message}", style="red")


def print_table(title: str, headers: list[str], rows: list[list]) -> None:
    table = Table(title=title, show_header=True, header_style="bold")
    for header in headers:
        table.add_column(header)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    _console.print(table)


def handle_cli_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error(str(e))
            raise SystemExit(1)

    return wrapper


def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error(str(e))
            raise typer.Exit(1)

    return wrapper


def prompter(prompts: list[str], hide_input: bool = False) -> dict[str, str]:
    return {prompt: typer.prompt(prompt, hide_input=hide_input) for prompt in prompts}