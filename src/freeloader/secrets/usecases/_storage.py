import click

from freeloader.secrets.storage import Storage, PasswordRequiredError
from freeloader.shared.system.fl import Freeloader


def load_storage() -> Storage:
    freeloader = Freeloader()
    return Storage(freeloader.secrets_folder, freeloader.session_folder)


def ensure_unlocked(storage: Storage) -> None:
    try:
        storage.has("__probe__", "__probe__")
    except PasswordRequiredError:
        password = click.prompt("Vault password", hide_input=True)
        storage.save_password(password)
