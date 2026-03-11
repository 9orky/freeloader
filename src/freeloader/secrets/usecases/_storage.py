import click
from pathlib import Path

from ..storage import Storage, PasswordRequiredError
from freeloader.shared.runtime import Freeloader


def load_storage() -> Storage:
    runtime = Freeloader.from_env(Path.cwd())
    return Storage(
        runtime.secrets_folder,
        runtime.session_folder,
    )


def ensure_unlocked(storage: Storage) -> None:
    try:
        storage.has("__probe__", "__probe__")
    except PasswordRequiredError:
        password = click.prompt("Vault password", hide_input=True)
        storage.save_password(password)
