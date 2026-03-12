from dataclasses import dataclass

from . import DEFAULT_NAMESPACE


@dataclass(frozen=True)
class Secret:
    name: str
    value: str
    namespace: str = DEFAULT_NAMESPACE
