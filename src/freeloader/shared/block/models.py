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


