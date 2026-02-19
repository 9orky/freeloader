from dataclasses import dataclass


@dataclass(frozen=True)
class TerraformVariable:
    name: str
    type: str
    default: str | int | float | bool | list[str] | None
    description: str
    sensitive: bool
    required: bool
