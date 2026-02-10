from dataclasses import dataclass
from functools import wraps
from typing import Callable, ParamSpec, TypeVar

from rich.panel import Panel
from rich.text import Text

from freeloader.shared.console import err_console

P = ParamSpec("P")
R = TypeVar("R")


class FreloaderError(Exception):
    def render(self) -> None:
        err_console.print(Panel(
            str(self),
            title="[bold red]Error[/]",
            border_style="red",
        ))


class ConfigurationError(FreloaderError):
    pass


@dataclass
class SubprocessDetail:
    command: list[str]
    exit_code: int
    stderr: str
    stdout: str
    cwd: str


class SubprocessError(FreloaderError):
    def __init__(self, message: str, detail: SubprocessDetail) -> None:
        self.detail = detail
        super().__init__(message)

    def render(self) -> None:
        text = Text()
        text.append("Command: ", style="bold")
        text.append(" ".join(self.detail.command) + "\n")
        text.append("Directory: ", style="bold")
        text.append(self.detail.cwd + "\n")
        text.append("Exit code: ", style="bold")
        text.append(str(self.detail.exit_code) + "\n")
        if self.detail.stderr:
            text.append("\n")
            text.append("stderr:\n", style="bold red")
            for line in self.detail.stderr.strip().splitlines()[-30:]:
                text.append(f"  {line}\n")
        if self.detail.stdout:
            text.append("\n")
            text.append("stdout:\n", style="bold")
            for line in self.detail.stdout.strip().splitlines()[-15:]:
                text.append(f"  {line}\n")

        err_console.print(Panel(
            text,
            title=f"[bold red]{self}[/]",
            border_style="red",
        ))


@dataclass(frozen=True)
class FeasibilityIssue:
    runner: str
    check: str
    detail: str


class FeasibilityError(FreloaderError):
    def __init__(self, issues: list[FeasibilityIssue]) -> None:
        self.issues = issues
        summary = "; ".join(
            f"[{i.runner}] {i.check}: {i.detail}" for i in issues)
        super().__init__(f"Pre-flight checks failed: {summary}")

    def render(self) -> None:
        text = Text()
        text.append("The following checks failed:\n\n", style="bold")
        for issue in self.issues:
            text.append(f"  [{issue.runner}] ", style="bold yellow")
            text.append(f"{issue.check}\n", style="bold")
            text.append(f"    → {issue.detail}\n", style="red")
        err_console.print(Panel(
            text,
            title="[bold red]Pre-flight Failed[/]",
            border_style="red",
        ))


def handle_errors(fn: Callable[P, R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        import typer

        try:
            return fn(*args, **kwargs)
        except FreloaderError as exc:
            exc.render()
            raise typer.Exit(1) from None

    return wrapper
