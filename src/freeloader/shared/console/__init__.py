import functools

from rich.tree import Tree
import typer
from rich.console import Console
from rich.table import Table

_console = Console()
_err_console = Console(stderr=True)

from .input_selector import InputSelector, prompt  # noqa: E402
from .progress import ProgressUpdate, StatusStream, run_status_stream  # noqa: E402


def info(message: str) -> None:
    _console.print(message, style="dim")


def ok(message: str) -> None:
    _console.print(f"✓ {message}", style="green")


def warn(message: str) -> None:
    _console.print(f"⚠ {message}", style="yellow")


def error(message: str) -> None:
    _err_console.print(f"✗ {message}", style="red")


def print_dict(data: dict, title: str = "", as_tree: bool = True) -> None:
    if title:
        _console.print(f"[bold]{title}[/bold]")

    if as_tree:
        tree = Tree(title)
        dict_to_tree(data, tree)
        _console.print(tree)
    else:
        for key, value in data.items():
            _console.print(f"[bold]{key}:[/bold] {value}")


def dict_to_tree(data: dict | list | str, tree: Tree):
    if isinstance(data, dict):
        for key, value in data.items():
            branch = tree.add(f"[bold cyan]{key}[/bold cyan]")
            dict_to_tree(value, branch)
    elif isinstance(data, list):
        for item in data:
            dict_to_tree(item, tree)
    else:
        tree.add(f"[green]{data}[/green]")


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
    return {prompt_text: prompt(prompt_text, hide_input=hide_input) for prompt_text in prompts}


__all__ = [
    "ProgressUpdate",
    "StatusStream",
    "InputSelector",
    "dict_to_tree",
    "error",
    "handle_cli_error",
    "handle_errors",
    "info",
    "ok",
    "prompt",
    "print_dict",
    "print_table",
    "prompter",
    "run_status_stream",
    "warn",
]
