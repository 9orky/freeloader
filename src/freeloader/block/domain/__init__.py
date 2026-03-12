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

from .events import (  # noqa: E402
    BlockApplyCompleted,
    BlockApplyStarted,
    BlockDependencyInputsStarted,
    BlockDestroyCompleted,
    BlockDestroyEvent,
    BlockDestroyFailed,
    BlockDestroyStarted,
    BlockPreparationCompleted,
    BlockPreparationStarted,
    BlockProvisionEvent,
    DestroyFinished,
    DestroyStarted,
    ProvisionPhase,
    ProvisioningFailed,
    ProvisioningFinished,
    ProvisioningStarted,
)
from .provisioning import (  # noqa: E402
    AppliedStepReport,
    DestroyReport,
    DestroyStepReport,
    ProvisioningPlan,
    ProvisioningReport,
    ProvisioningStep,
)

__all__ = [
    "AppliedStepReport",
    "BlockApplyCompleted",
    "BlockApplyStarted",
    "BlockDependencyInputsStarted",
    "BlockDestroyCompleted",
    "BlockDestroyEvent",
    "BlockDestroyFailed",
    "BlockDestroyStarted",
    "BlockPreparationCompleted",
    "BlockPreparationStarted",
    "BlockProvisionEvent",
    "DestroyFinished",
    "DestroyReport",
    "DestroyStarted",
    "DestroyStepReport",
    "LAYER_ORDER",
    "Layer",
    "ProvisionPhase",
    "ProvisioningFailed",
    "ProvisioningFinished",
    "ProvisioningPlan",
    "ProvisioningReport",
    "ProvisioningStarted",
    "ProvisioningStep",
]
