from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping

from .errors import MissingCredentialsError


class ProviderName(str):
    def __new__(cls, value: str) -> "ProviderName":
        normalized = value.strip().lower()
        if not normalized:
            raise ValueError("Provider name must be non-empty.")
        return str.__new__(cls, normalized)


class CredentialKey(str):
    def __new__(cls, value: str) -> "CredentialKey":
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("Credential key must be non-empty.")
        return str.__new__(cls, normalized)


class CredentialValue(str):
    def __new__(cls, value: str) -> "CredentialValue":
        if not value.strip():
            raise ValueError("Credential value must be non-empty.")
        return str.__new__(cls, value)


class LocalCommand(str):
    def __new__(cls, value: str) -> "LocalCommand":
        normalized = value.strip()
        if not normalized:
            raise ValueError("Local command must be non-empty.")
        return str.__new__(cls, normalized)


@dataclass(frozen=True)
class Credentials:
    _values: Mapping[CredentialKey, CredentialValue] = field(
        default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        normalized: dict[CredentialKey, CredentialValue] = {}
        for key, value in dict(self._values).items():
            normalized[CredentialKey(str(key))] = CredentialValue(str(value))
        object.__setattr__(self, "_values", MappingProxyType(normalized))

    def __bool__(self) -> bool:
        return bool(self._values)

    def __contains__(self, key: CredentialKey | str) -> bool:
        return CredentialKey(str(key)) in self._values

    def __getitem__(self, key: CredentialKey | str) -> str:
        return str(self._values[CredentialKey(str(key))])

    def require(
        self,
        keys: Iterable[CredentialKey | str],
        *,
        provider_name: str | None = None,
    ) -> "Credentials":
        normalized_keys = [CredentialKey(str(key)) for key in keys]
        missing = [str(key)
                   for key in normalized_keys if key not in self._values]
        if missing:
            raise MissingCredentialsError(missing, provider_name=provider_name)
        return self.subset(normalized_keys)

    def subset(self, keys: Iterable[CredentialKey | str]) -> "Credentials":
        normalized_keys = [CredentialKey(str(key)) for key in keys]
        return Credentials({key: self._values[key] for key in normalized_keys if key in self._values})

    def to_dict(self) -> dict[str, str]:
        return {str(key): str(value) for key, value in self._values.items()}
