from __future__ import annotations

from freeloader.secrets.application.interface import Secrets

from ..domain import CredentialKey, CredentialValue, Credentials
from ..domain.repository import CredentialRepository


class SecretsCredentialRepository(CredentialRepository):
    def __init__(self, secrets: Secrets | None = None) -> None:
        self._secrets = secrets or Secrets.for_default_namespace()

    def read_credentials(self, keys: list[CredentialKey]) -> Credentials:
        normalized_keys = [CredentialKey(str(key)) for key in keys]
        if not normalized_keys:
            return Credentials()

        secret_names = [
            self._secret_name(key)
            for key in normalized_keys
            if self._secrets.has_secrets([self._secret_name(key)])
        ]
        if not secret_names:
            return Credentials()

        stored_values = self._secrets.read_secrets(secret_names)
        return Credentials(
            {
                key: CredentialValue(stored_values[self._secret_name(key)])
                for key in normalized_keys
                if self._secret_name(key) in stored_values
            }
        )

    def write_credentials(self, credentials: Credentials) -> None:
        values = credentials.to_dict()
        if not values:
            return

        self._secrets.write_secrets(
            {self._secret_name(key): value for key, value in values.items()}
        )

    @staticmethod
    def _secret_name(key: CredentialKey | str) -> str:
        return str(CredentialKey(str(key))).lower()