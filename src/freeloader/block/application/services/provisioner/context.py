from freeloader.block.domain.entity import OutputReference
from freeloader.shared.types import ConfigValue


class ExecutionOutputs:
    """Accumulates block outputs during the provisioning loop."""

    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, ConfigValue | None]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, ConfigValue | None]) -> None:
        self._outputs[block_id] = outputs

    def resolve_inputs(self, inputs: list[OutputReference]) -> dict[str, ConfigValue | None]:
        result: dict[str, ConfigValue | None] = {}
        for ref in inputs:
            tfvar_name = ref.requirement_key.replace(".", "_")
            result[tfvar_name] = self._outputs.get(
                ref.provider_id, {}).get(ref.output_name)
        return result
