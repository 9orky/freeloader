import os
from pathlib import Path

class PasswordRequiredError(Exception): ...

class SecretSession:
    def __init__(self, session_file_path: Path) -> None:
        self._session_file_path = session_file_path

    def get_password(self) -> str:
        try:
            return os.environ["FREELOADER_VAULT_PASSWORD"]
        except KeyError:
            try:
                return self._session_file_path.read_text().strip()
            except FileNotFoundError:
                raise PasswordRequiredError()

    def save_password(self, password: str) -> None:
        self._session_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._session_file_path.write_text(password)
