import os
from pathlib import Path


class PasswordRequiredError(Exception):
    ...


class SecretSession:
    def __init__(self, session_file_path: Path, legacy_file_paths: tuple[Path, ...] = ()) -> None:
        self._session_file_path = session_file_path
        self._legacy_file_paths = legacy_file_paths

    def get_password(self) -> str:
        try:
            return os.environ["FREELOADER_VAULT_PASSWORD"]
        except KeyError:
            password = self._read_password(self._session_file_path)
            if password is not None:
                return password

            for legacy_file_path in self._legacy_file_paths:
                password = self._read_password(legacy_file_path)
                if password is not None:
                    self.save_password(password)
                    return password

            raise PasswordRequiredError()

    def _read_password(self, password_file_path: Path) -> str | None:
        try:
            return password_file_path.read_text().strip()
        except FileNotFoundError:
            return None

    def save_password(self, password: str) -> None:
        self._session_file_path.parent.mkdir(parents=True, exist_ok=True)
        self._session_file_path.write_text(password)
