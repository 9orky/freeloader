from dataclasses import dataclass

DEFAULT_NAMESPACE = "global"


@dataclass(frozen=True)
class Secret:
    name: str
    value: str
    namespace: str = DEFAULT_NAMESPACE


@dataclass(frozen=True)
class StoredSecret:
    name: str
    value: str
    namespace: str
