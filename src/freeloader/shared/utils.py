import functools
from pathlib import Path
from uuid import UUID, uuid5, NAMESPACE_URL
import click


def path_to_id(path_str: str) -> UUID:
    normalized = Path(path_str).resolve().as_posix()
    return uuid5(NAMESPACE_URL, normalized)


def handle_cli_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            click.secho(f"\nError: {str(e)}\n", fg="white", bg="red", bold=True, err=True)
            exit(1)

    return wrapper
