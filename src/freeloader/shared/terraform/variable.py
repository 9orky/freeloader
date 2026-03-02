from dataclasses import dataclass

from freeloader.shared.types import ConfigValue


@dataclass(frozen=True)
class TerraformVariable:
    name: str
    type: str
    default: ConfigValue | None
    description: str
    sensitive: bool
    required: bool
