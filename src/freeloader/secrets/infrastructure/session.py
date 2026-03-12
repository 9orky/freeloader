import os
from pathlib import Path

from ..domain.repository import SessionRepository
from ..domain.value_object import Password


_SESSION_FILE = "vault-password"


class SecretSession(SessionRepository):
    def __init__(self, session_folder: Path, legacy_file_paths: tuple[Path, ...] = ()) -> None:
        self._session_file_path = session_folder / _SESSION_FILE
        self._legacy_file_paths = legacy_file_paths

    def get_password(self) -> Password:
        try:
            return Password(os.environ["FREELOADER_VAULT_PASSWORD"])
        except KeyError:
            password = self._read_password(self._session_file_path)
            if password is not None:
                return Password(password)

            for legacy_file_path in self._legacy_file_paths:
                password = self._read_password(legacy_file_path)
                if password is not None:
                    self.save_password(Password(password))
                    return Password(password)

            raise RuntimeError("Password for Vault is not stored in Session")

    def _read_password(self, password_file_path: Path) -> str | None:
        try:
            return password_file_path.read_text().strip()
        except FileNotFoundError:
            return None

    def save_password(self, password: Password) -> None:
        self._session_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._session_file_path.write_text(password.value)
