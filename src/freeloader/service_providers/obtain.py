from dataclasses import dataclass

from .base import ObtainTokenStep
from .registry import load_provider


@dataclass(frozen=True)
class Input(ObtainTokenStep):
    value: str
    action: str = "input"


@dataclass(frozen=True)
class Info(ObtainTokenStep):
    value: str
    action: str = "info"


@dataclass(frozen=True)
class OpenURL(ObtainTokenStep):
    value: str
    action: str = "open_url"


def get_obtain_steps(provider_name: str) -> list[ObtainTokenStep]:
    return load_provider(provider_name).obtain_token_steps
