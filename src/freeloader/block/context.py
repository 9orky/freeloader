from freeloader.shared.types import ConfigValue


class ExecutionContext:
    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, ConfigValue | None]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, ConfigValue | None]) -> None:
        self._outputs[block_id] = outputs

    def get_output(self, block_id: str, key: str) -> ConfigValue | None:
        return self._outputs[block_id][key]

    def get_all_outputs(self, block_id: str) -> dict[str, ConfigValue | None]:
        return dict(self._outputs.get(block_id, {}))

    def has_outputs(self, block_id: str) -> bool:
        return block_id in self._outputs

    def resolve_inputs(self, inputs_map: dict[str, str]) -> dict[str, ConfigValue | None]:
        result: dict[str, ConfigValue | None] = {}
        for req_key, provider_id in inputs_map.items():
            output_name = req_key.split(".", 1)[1]
            result[req_key] = self.get_output(provider_id, output_name)
        return result
