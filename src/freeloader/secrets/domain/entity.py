from dataclasses import dataclass

from . import DEFAULT_NAMESPACE


@dataclass(frozen=True)
class Secret:
    name: str
    value: str
    namespace: str = DEFAULT_NAMESPACE


@dataclass(frozen=True)
class SecretAvailabilityReport:
    required_keys: tuple[str, ...]
    present_keys: tuple[str, ...]
    missing_keys: tuple[str, ...]

    @property
    def available(self) -> bool:
        return not self.missing_keys
