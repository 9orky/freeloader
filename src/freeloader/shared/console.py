from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
err_console = Console(stderr=True)


def info(msg: str) -> None:
    console.print(f"[bold blue]ℹ[/] {msg}")


def success(msg: str) -> None:
    console.print(f"[bold green]✓[/] {msg}")


def warn(msg: str) -> None:
    err_console.print(f"[bold yellow]⚠[/] {msg}")


def error(msg: str) -> None:
    err_console.print(f"[bold red]✗[/] {msg}")


def print_table(title: str, columns: list[str], rows: list[list[str]]) -> None:
    table = Table(title=title, show_header=True, header_style="bold cyan")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*row)
    console.print(table)


def print_panel(title: str, content: str, style: str = "blue") -> None:
    console.print(Panel(content, title=title, border_style=style))


def confirm(prompt: str, default: bool = False) -> bool:
    return console.input(f"{prompt} [{'Y/n' if default else 'y/N'}]: ").strip().lower() in (
        ("", "y", "yes") if default else ("y", "yes")
    )


def spinner(msg: str) -> Console.status:
    return console.status(msg, spinner="dots")
