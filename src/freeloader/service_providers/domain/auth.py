from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import ProviderDefinitionError
from .value_object import CredentialKey, ProviderName


class ObtainCredentialAction(str, Enum):
    input = "input"
    info = "info"
    open_url = "open_url"


@dataclass(frozen=True)
class ObtainCredentialStep:
    action: ObtainCredentialAction | str
    value: str

    def __post_init__(self) -> None:
        try:
            action = self.action if isinstance(
                self.action, ObtainCredentialAction) else ObtainCredentialAction(self.action)
        except ValueError as exc:
            raise ProviderDefinitionError(
                f"Invalid obtain credential action '{self.action}'.") from exc

        value = self.value.strip()
        if not value:
            raise ProviderDefinitionError(
                "Obtain credential step value must be non-empty.")

        object.__setattr__(self, "action", action)
        object.__setattr__(self, "value", value)


@dataclass(frozen=True)
class AuthSpec:
    credential_keys: tuple[CredentialKey, ...]
    obtain_steps: tuple[ObtainCredentialStep, ...] = ()

    def __post_init__(self) -> None:
        normalized_keys = tuple(CredentialKey(str(key))
                                for key in self.credential_keys)
        if not normalized_keys:
            raise ProviderDefinitionError(
                "Auth spec must declare at least one credential key or be omitted.")
        if len(dict.fromkeys(normalized_keys)) != len(normalized_keys):
            raise ProviderDefinitionError(
                "Auth spec credential keys must be unique.")

        normalized_steps = tuple(
            step if isinstance(
                step, ObtainCredentialStep) else ObtainCredentialStep(**step)
            for step in self.obtain_steps
        )

        object.__setattr__(self, "credential_keys", normalized_keys)
        object.__setattr__(self, "obtain_steps", normalized_steps)

    @property
    def requires_auth(self) -> bool:
        return bool(self.credential_keys)


@dataclass(frozen=True)
class AuthorizationResult:
    provider: ProviderName | str
    stored_credentials: tuple[CredentialKey, ...]

    def __post_init__(self) -> None:
        provider = ProviderName(str(self.provider))
        stored_credentials = tuple(CredentialKey(str(key))
                                   for key in self.stored_credentials)
        if len(dict.fromkeys(stored_credentials)) != len(stored_credentials):
            raise ProviderDefinitionError(
                "Stored credential keys must be unique.", provider_name=str(provider))
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "stored_credentials", stored_credentials)
