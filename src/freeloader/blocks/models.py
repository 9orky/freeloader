from enum import Enum

from pydantic import BaseModel


class RunnerType(str, Enum):
    terraform = "terraform"
    script = "script"
    api = "api"
    generator = "generator"


class Layer(str, Enum):
    infra = "infra"
    platform = "platform"
    source = "source"
    registry = "registry"
    build = "build"
    deploy = "deploy"
    network = "network"
    data = "data"
    observe = "observe"


LAYER_ORDER: dict[Layer, int] = {layer: i for i, layer in enumerate(Layer)}


class PortSpec(BaseModel):
    type: str = "string"
    description: str = ""
    optional: bool = False
    usage: str | None = None


class ConfigField(BaseModel):
    type: str = "string"
    required: bool = False
    default: str | int | float | bool | list[str] | None = None
    description: str = ""
    choices: list[str] | None = None


class BlockMeta(BaseModel):
    name: str
    description: str = ""
    runner: RunnerType
    layer: Layer
    version: str = "0.1.0"
    provider: str | None = None
    required_secrets: list[str] = []


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: dict[str, ConfigField] = {}
