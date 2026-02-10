import importlib
import pkgutil
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class CredentialStatus:
    valid: bool
    identity: str = ""
    error: str = ""


class ProviderChecker(Protocol):
    @property
    def name(self) -> str: ...

    def check_credentials(
        self, secrets: dict[str, str], api_url: str) -> CredentialStatus: ...


_CHECKER_CLASSES: list[type[ProviderChecker]] = []


def register(cls: type[ProviderChecker]) -> type[ProviderChecker]:
    _CHECKER_CLASSES.append(cls)
    return cls


def _discover() -> None:
    package = importlib.import_module(__package__)
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        importlib.import_module(f"{__package__}.{info.name}")


class CheckerRegistry:
    def __init__(self, checkers: list[ProviderChecker]) -> None:
        self._checkers = {p.name: p for p in checkers}

    @classmethod
    def discover(cls) -> "CheckerRegistry":
        _discover()
        return cls([p() for p in _CHECKER_CLASSES])

    def check(self, provider: str, secrets: dict[str, str], api_url: str = "") -> CredentialStatus:
        return self._checkers[provider].check_credentials(secrets, api_url)
