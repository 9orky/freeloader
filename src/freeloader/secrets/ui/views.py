from pydantic.dataclasses import dataclass


@dataclass(frozen=True)
class SecretView:
    name: str
    value: str
    namespace: str
