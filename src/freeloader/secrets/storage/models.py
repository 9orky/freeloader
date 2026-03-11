from dataclasses import dataclass

DEFAULT_NAMESPACE = "global"


@dataclass(frozen=True)
class Secret:
    name: str
    value: str = ""
    namespace: str = DEFAULT_NAMESPACE
