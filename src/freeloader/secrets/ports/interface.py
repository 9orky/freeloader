from freeloader.shared import Freeloader

from .. import usecases
from ..storage import Storage


def _load_storage() -> Storage:
    freeloader = Freeloader()
    return Storage(freeloader.secrets_folder, freeloader.session_folder)


def read_secrets(namespace: str, secret_names: list[str]) -> dict[str, str]:
    pass


def write_secret(namespace: str, secret_name: str, secret_value: str) -> None:
    usecases.write_secret(secret_name, secret_value, namespace)


def has_secrets(namespace: str, secret_names: list[str]) -> bool:
    storage = _load_storage()