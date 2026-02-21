from enum import Enum


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





